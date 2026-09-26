from __future__ import annotations

import base64
import io
import queue
import threading
import time
from collections import deque
from typing import Optional

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Image


DEFAULT_CAMERA_TOPICS = {
    "World Camera": "/world/camera/color/image_raw/compressed",
    "Left Gripper Camera": "/left/camera/color/image_raw/compressed",
    "Right Gripper Camera": "/right/camera/color/image_raw/compressed"
}


class CameraDisplayNode(Node):
    """ROS 2 node that subscribes to camera topics and stores latest frames"""
    
    def __init__(self, camera_topics: Optional[dict] = None, context=None, node_name: str = 'camera_display_node'):
        node_kwargs = {}
        if context is not None:
            node_kwargs['context'] = context
        super().__init__(node_name, **node_kwargs)
        
        # Camera topic subscriptions - defaults to the 3-camera operator layout.
        self.camera_topics = dict(camera_topics) if (camera_topics is not None and len(camera_topics) > 0) else dict(DEFAULT_CAMERA_TOPICS)
        
        self.camera_frames = {}
        self.camera_base64_frames = {}
        self.camera_last_frame_time = {}
        self.camera_subscribers = {}
        self.frame_lock = threading.Lock()
        
        # Track which cameras are active in the UI (starts with default camera topics)
        self.ui_active_cameras = set(self.camera_topics.keys())
        self.is_replay_mode = False

        # Thread-safe queue for dynamic subscription requests from HTTP threads.
        # All actual create_subscription() calls happen via the timer below,
        # ensuring they run on the executor's own thread (race-free).
        self._subscription_queue: queue.Queue = queue.Queue()
        self.create_timer(0.05, self._process_subscription_queue)
        
        # Initialize empty frames
        for camera_name in self.camera_topics.keys():
            self.camera_frames[camera_name] = None
            self.camera_base64_frames[camera_name] = None
            self.camera_last_frame_time[camera_name] = 0.0
        
        # Create subscribers for each camera topic
        self._setup_subscribers()
        
        self.get_logger().info(f'Camera Display Node initialized. Watching {len(self.camera_topics)} cameras')

    def _process_subscription_queue(self):
        """Timer callback: drain the pending subscription queue on the executor thread."""
        while not self._subscription_queue.empty():
            try:
                task = self._subscription_queue.get_nowait()
                action = task.get('action')
                name = task.get('name')
                topic = task.get('topic')

                if action == 'register' and name and topic:
                    # Destroy old sub if topic changed
                    if name in self.camera_subscribers and self.camera_topics.get(name) != topic:
                        try:
                            self.destroy_subscription(self.camera_subscribers.pop(name))
                        except Exception:
                            pass
                        self.camera_frames.pop(name, None)
                        self.camera_base64_frames.pop(name, None)

                    self.camera_topics[name] = topic
                    self.ui_active_cameras.add(name)
                    if name not in self.camera_subscribers:
                        try:
                            if topic.rstrip('/').endswith('/compressed'):
                                msg_type = CompressedImage
                                cb = lambda msg, n=name: self._camera_callback(msg, n)
                            else:
                                msg_type = Image
                                cb = lambda msg, n=name: self._raw_camera_callback(msg, n)

                            sub = self.create_subscription(
                                msg_type, topic, cb,
                                qos_profile=rclpy.qos.QoSProfile(
                                    depth=1,
                                    reliability=rclpy.qos.ReliabilityPolicy.BEST_EFFORT,
                                    durability=rclpy.qos.DurabilityPolicy.VOLATILE,
                                    history=rclpy.qos.HistoryPolicy.KEEP_LAST,
                                )
                            )
                            self.camera_subscribers[name] = sub
                            self.camera_frames.setdefault(name, None)
                            self.camera_base64_frames.setdefault(name, None)
                            self.camera_last_frame_time.setdefault(name, 0.0)
                            self.get_logger().info(
                                f"[queue] Subscribed '{name}' → {topic}"
                            )
                        except Exception as e:
                            self.get_logger().warn(f"[queue] Failed to subscribe '{name}': {e}")
 
                elif action == 'unregister' and name:
                    self.ui_active_cameras.discard(name)
                    if name in self.camera_subscribers:
                        try:
                            self.destroy_subscription(self.camera_subscribers.pop(name))
                            self.get_logger().info(f"[queue] Destroyed subscription for '{name}'")
                        except Exception as e:
                            self.get_logger().warn(f"[queue] Failed to destroy subscription for '{name}': {e}")
                    self.camera_topics.pop(name, None)
                    self.camera_frames.pop(name, None)
                    self.camera_base64_frames.pop(name, None)
                    self.camera_last_frame_time.pop(name, None)
                    self.get_logger().info(f"[queue] Unregistered camera '{name}' from UI")

            except queue.Empty:
                break
            except Exception as e:
                self.get_logger().warn(f'Subscription queue error: {e}')


    def _setup_subscribers(self):
        """Setup subscribers for all camera topics"""
        for camera_name, topic_name in self.camera_topics.items():
            try:
                if topic_name.rstrip("/").endswith("/compressed"):
                    msg_type = CompressedImage
                    callback = lambda msg, name=camera_name: self._camera_callback(msg, name)
                else:
                    msg_type = Image
                    callback = lambda msg, name=camera_name: self._raw_camera_callback(msg, name)

                sub = self.create_subscription(
                    msg_type,
                    topic_name,
                    callback,
                    qos_profile=rclpy.qos.QoSProfile(
                        depth=1,
                        reliability=rclpy.qos.ReliabilityPolicy.BEST_EFFORT,
                        durability=rclpy.qos.DurabilityPolicy.VOLATILE,
                        history=rclpy.qos.HistoryPolicy.KEEP_LAST,
                    )
                )
                self.camera_subscribers[camera_name] = sub
                self.get_logger().info(f'Subscribed to {camera_name}: {topic_name}')
            except Exception as e:
                self.get_logger().warn(f'Failed to subscribe to {camera_name} ({topic_name}): {e}')
    
    def _camera_callback(self, msg: CompressedImage, camera_name: str):
        """Callback for camera messages"""
        if getattr(self, 'is_replay_mode', False):
            return
        try:
            
            # Safely get the raw compressed JPEG bytes
            if hasattr(msg.data, 'tobytes'):
                jpeg_bytes = msg.data.tobytes()
            elif isinstance(msg.data, (bytes, bytearray)):
                jpeg_bytes = msg.data
            else:
                jpeg_bytes = bytes(msg.data)
                
            # Pre-encode to base64 to avoid HTTP thread lag
            img_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
            frame_url = f"data:image/jpeg;base64,{img_base64}"
            
            with self.frame_lock:
                self.camera_frames[camera_name] = jpeg_bytes
                self.camera_base64_frames[camera_name] = frame_url
                self.camera_last_frame_time[camera_name] = time.time()
        except Exception as e:
            self.get_logger().warn(f'Error processing frame from {camera_name}: {e}')

    def _raw_camera_callback(self, msg: Image, camera_name: str):
        """Callback for raw camera messages"""
        if getattr(self, 'is_replay_mode', False):
            return
        try:
            if not hasattr(self, '_callback_count'):
                self._callback_count = {}
            self._callback_count[camera_name] = self._callback_count.get(camera_name, 0) + 1
            if self._callback_count[camera_name] % 30 == 1:
                self.get_logger().info(f'Received raw frame {self._callback_count[camera_name]} for {camera_name} (encoding: {msg.encoding})')
            
            height = int(msg.height)
            width = int(msg.width)
            encoding = str(msg.encoding).lower()
            
            if "bgra" in encoding or "rgba" in encoding or "8uc4" in encoding:
                channels = 4
            elif "mono" in encoding or "8uc1" in encoding or "mono8" in encoding:
                channels = 1
            else:
                channels = 3
                
            row_bytes = int(msg.step) if int(msg.step) > 0 else width * channels
            array = np.frombuffer(msg.data, dtype=np.uint8)
            image = array.reshape(height, row_bytes)[:, : width * channels]
            
            if channels == 1:
                mono = image.reshape(height, width)
                frame_bgr = cv2.cvtColor(mono, cv2.COLOR_GRAY2BGR)
            elif channels == 4:
                image_4c = image.reshape(height, width, 4)
                if "bgra" in encoding:
                    frame_bgr = cv2.cvtColor(image_4c, cv2.COLOR_BGRA2BGR)
                else: # rgba
                    frame_bgr = cv2.cvtColor(image_4c, cv2.COLOR_RGBA2BGR)
            else: # channels == 3
                image_3c = image.reshape(height, width, 3)
                if "rgb" in encoding:
                    frame_bgr = cv2.cvtColor(image_3c, cv2.COLOR_RGB2BGR)
                else:
                    frame_bgr = image_3c
            
            _, buffer = cv2.imencode('.jpg', frame_bgr)
            jpeg_bytes = buffer.tobytes()
            
            # Pre-encode to base64 to avoid HTTP thread lag
            img_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
            frame_url = f"data:image/jpeg;base64,{img_base64}"
            
            with self.frame_lock:
                self.camera_frames[camera_name] = jpeg_bytes
                self.camera_base64_frames[camera_name] = frame_url
                self.camera_last_frame_time[camera_name] = time.time()
        except Exception as e:
            self.get_logger().warn(f'Error processing raw frame from {camera_name}: {e}')
    
    def get_all_camera_frames(self) -> dict[str, Optional[np.ndarray]]:
        """Get all current camera frames as numpy arrays"""
        with self.frame_lock:
            frames = {}
            now = time.time()
            for k, v in self.camera_frames.items():
                last_time = self.camera_last_frame_time.get(k, 0.0)
                if v is not None and (now - last_time <= 2.0):
                    try:
                        np_arr = np.frombuffer(v, np.uint8)
                        frames[k] = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    except Exception:
                        frames[k] = None
                else:
                    frames[k] = None
            return frames
    
    def get_camera_frame_base64(self, camera_name: str) -> Optional[str]:
        """Get a single camera frame as base64 encoded JPEG"""
        with self.frame_lock:
            last_time = self.camera_last_frame_time.get(camera_name, 0.0)
            if time.time() - last_time > 2.0:
                return None
            return self.camera_base64_frames.get(camera_name)


    def get_camera_frame_jpeg_bytes(self, camera_name: str) -> Optional[bytes]:
        """Get a single camera frame as raw JPEG bytes"""
        with self.frame_lock:
            last_time = self.camera_last_frame_time.get(camera_name, 0.0)
            if time.time() - last_time > 2.0:
                return None
            jpeg_bytes = self.camera_frames.get(camera_name)
        return jpeg_bytes
    
    def get_camera_count(self) -> int:
        """Get the number of cameras being watched"""
        return len(self.camera_topics)
    
    def get_camera_names(self) -> list[str]:
        """Get list of camera names"""
        return list(self.camera_topics.keys())
    
    def get_camera_status(self) -> dict[str, bool]:
        """Check which cameras have received frames recently"""
        with self.frame_lock:
            now = time.time()
            return {
                name: (self.camera_frames[name] is not None and (now - self.camera_last_frame_time.get(name, 0.0) <= 2.0))
                for name in self.camera_frames.keys()
            }

    def set_replay_mode(self, enabled: bool):
        self.is_replay_mode = enabled
        if not enabled:
            with self.frame_lock:
                for k in list(self.camera_frames.keys()):
                    self.camera_frames[k] = None
                    self.camera_base64_frames[k] = None

    def inject_frame(self, camera_name: str, jpeg_bytes: bytes):
        try:
            img_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
            frame_url = f"data:image/jpeg;base64,{img_base64}"
            with self.frame_lock:
                self.camera_frames[camera_name] = jpeg_bytes
                self.camera_base64_frames[camera_name] = frame_url
                self.camera_last_frame_time[camera_name] = time.time()
        except Exception as e:
            pass


def create_camera_html_section() -> str:
    """Create HTML for camera display section"""
    return """
    <!-- Camera Display Section -->
    <div class="camera-section">
      <div class="camera-header">
        <h2>Camera Feeds</h2>
        <span id="camera-count" class="camera-count">0 cameras</span>
      </div>
      <div class="camera-grid" id="camera-grid">
        <!-- Camera squares will be populated here -->
      </div>
    </div>
    """


def create_camera_css() -> str:
    """Create CSS for camera display"""
    return """
    .camera-section {
      width: 100%; max-width: 1100px; margin: 40px 0;
      background: var(--panel-bg);
      backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--panel-border); border-radius: var(--radius);
      padding: 32px; box-shadow: var(--shadow-lg);
    }
    
    .camera-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 24px; padding-bottom: 16px;
      border-bottom: 1px solid var(--panel-border);
    }
    
    .camera-header h2 {
      font-size: 1.4rem; font-weight: 600; color: #fff;
    }
    
    .camera-count {
      font-size: 0.9rem; color: var(--text-muted);
      background: rgba(59, 130, 246, 0.1); padding: 6px 12px;
      border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .camera-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }
    
    .camera-box {
      aspect-ratio: 1; border-radius: 12px;
      overflow: hidden; border: 1px solid var(--panel-border);
      background: #000; position: relative;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      transition: var(--transition);
    }
    
    .camera-box:hover {
      border-color: var(--accent);
      box-shadow: 0 8px 20px var(--accent-glow);
    }
    
    .camera-box img {
      width: 100%; height: 100%; object-fit: cover;
      display: block;
    }
    
    .camera-label {
      position: absolute; bottom: 0; left: 0; right: 0;
      padding: 10px 12px; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
      color: white; font-weight: 500; font-size: 0.9rem;
      text-transform: capitalize;
    }
    
    .camera-status-indicator {
      position: absolute; top: 10px; right: 10px;
      width: 12px; height: 12px; border-radius: 50%;
      background: var(--success); box-shadow: 0 0 8px var(--success);
      animation: pulse 2s infinite;
    }
    
    .camera-status-indicator.offline {
      background: var(--danger);
      box-shadow: 0 0 8px var(--danger);
      animation: none;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    @media (max-width: 1000px) {
      .camera-grid { grid-template-columns: repeat(2, 1fr); }
    }
    
    @media (max-width: 600px) {
      .camera-grid { grid-template-columns: 1fr; }
    }
    """


def create_camera_js(update_interval_ms: int = 500) -> str:
    """Create JavaScript for camera feed updates"""
    return f"""
    let cameraUpdateInterval = {update_interval_ms};
    
    async function initializeCameraDisplay() {{
      try {{
        const response = await fetch('/api/cameras/info');
        const info = await response.json();
        
        const grid = document.getElementById('camera-grid');
        grid.innerHTML = '';
        
        // Update camera count
        document.getElementById('camera-count').textContent = 
          info.count + ' camera' + (info.count !== 1 ? 's' : '');
        
        // Create camera boxes
        for (let i = 0; i < info.cameras.length; i++) {{
          const cameraName = info.cameras[i];
          const box = document.createElement('div');
          box.className = 'camera-box';
          box.id = 'camera-' + cameraName;
          
          const img = document.createElement('img');
          img.src = '/api/cameras/frame/' + cameraName;
          img.alt = cameraName;
          
          const status = document.createElement('div');
          status.className = 'camera-status-indicator ' + 
            (info.status[cameraName] ? 'online' : 'offline');
          status.id = 'status-' + cameraName;
          
          const label = document.createElement('div');
          label.className = 'camera-label';
          label.textContent = cameraName.replace(/_/g, ' ');
          
          box.appendChild(img);
          box.appendChild(status);
          box.appendChild(label);
          grid.appendChild(box);
        }}
      }} catch (err) {{
        console.error('Error initializing camera display:', err);
      }}
    }}
    
    async function updateCameraFrames() {{
      try {{
        const response = await fetch('/api/cameras/all-frames');
        const data = await response.json();
        
        if (!data.ok) return;
        
        for (const [cameraName, frameData] of Object.entries(data.frames)) {{
          const img = document.querySelector('#camera-' + cameraName + ' img');
          if (img && frameData) {{
            img.src = frameData;
          }}
          
          // Update status indicator
          const status = document.getElementById('status-' + cameraName);
          if (status) {{
            if (frameData) {{
              status.classList.remove('offline');
            }} else {{
              status.classList.add('offline');
            }}
          }}
        }}
      }} catch (err) {{
        console.error('Error updating camera frames:', err);
      }}
    }}
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', () => {{
      initializeCameraDisplay();
      setInterval(updateCameraFrames, cameraUpdateInterval);
    }});
    """
