#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import json
import time
import os
from collections import deque
import importlib
from rosidl_runtime_py import message_to_ordereddict
from pymongo import MongoClient
import datetime
class TopicLogger(Node):
    def __init__(self):
        super().__init__('ihub_topic_logger')
        
        # MongoDB connection setup
        try:
            self.mongo_client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
            self.db = self.mongo_client['telemetry_db']
            self.state_collection = self.db['latest_state']
            self.history_collection = self.db['history']
            self.get_logger().info("Connected to MongoDB successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to MongoDB: {e}")
            
        self.log_dir = "/home/jetson/Documents/logs/dataset"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # All topics to monitor and log
        self.target_topics = [
            "/LeftArmSystem/motor_status",
            "/LeftArmSystem_ordered_joint_states",
            "/RightArmSystem/motor_status",
            "/RightArmSystem_ordered_joint_states",
            "/gravity_torque",
            "/gravity_torque_temp",
            "/jnt_cmt_to_ctrl",
            "/joint_cmd",
            "/joint_states",
            "/left_arm_mit_controller/joint_trajectory",
            "/left_gripper_mit_controller/joint_trajectory",
            "/right_arm_mit_controller/joint_trajectory",
            "/right_gripper_mit_controller/joint_trajectory",
            "/zed/zed_node/right/color/rect/image",
            "/zed/zed_node/left/color/rect/image",
            "/right/camera/color/image_raw",
            "/left/camera/color/image_raw"
        ]
        
        self.topic_stats = {}
        for t in self.target_topics:
            self.topic_stats[t] = {
                'timestamps': deque(maxlen=50),
                'hz_fps': 0.0,
                'latest_data': None
            }
            
        self.subs = {}
        
        # Periodically discover topics so we can dynamically import their msg types
        self.discovery_timer = self.create_timer(2.0, self.discover_and_subscribe)
        
        # Periodically save logs to JSON
        self.save_timer = self.create_timer(1.0, self.save_logs)
        
    def discover_and_subscribe(self):
        topic_names_and_types = self.get_topic_names_and_types()
        for topic_name, types in topic_names_and_types:
            if topic_name in self.target_topics and topic_name not in self.subs:
                msg_type_str = types[0] # e.g. 'sensor_msgs/msg/Image'
                try:
                    parts = msg_type_str.split('/')
                    if len(parts) >= 2:
                        pkg = parts[0]
                        # ROS2 topic types are typically pkg/msg/Type
                        sub = parts[1] if len(parts) == 3 else 'msg'
                        cls = parts[-1]
                        module = importlib.import_module(f"{pkg}.{sub}")
                        msg_class = getattr(module, cls)
                        
                        self.subs[topic_name] = self.create_subscription(
                            msg_class, 
                            topic_name, 
                            lambda msg, tn=topic_name: self.callback(msg, tn), 
                            10
                        )
                        self.get_logger().info(f"Subscribed to {topic_name} [{msg_type_str}]")
                except Exception as e:
                    self.get_logger().error(f"Failed to subscribe to {topic_name} [{msg_type_str}]: {e}")

    def callback(self, msg, topic_name):
        now = time.time()
        stats = self.topic_stats[topic_name]
        stats['timestamps'].append(now)
        
        # Calculate Hz / FPS
        if len(stats['timestamps']) > 1:
            dt = stats['timestamps'][-1] - stats['timestamps'][0]
            if dt > 0:
                stats['hz_fps'] = (len(stats['timestamps']) - 1) / dt
        
        # Avoid saving massive arrays for Images/TF. We only want metadata.
        if type(msg).__name__ in ['Image', 'CompressedImage']:
            stats['latest_data'] = f"Image Data (Size: {len(msg.data)} bytes)"
        elif type(msg).__name__ == 'TFMessage':
            stats['latest_data'] = f"TF Data ({len(msg.transforms)} transforms)"
        else:
            try:
                # Convert standard/custom ROS message to dict (extracts mos_temp, rotor_temp, etc.)
                msg_dict = message_to_ordereddict(msg)
                stats['latest_data'] = msg_dict
            except Exception:
                stats['latest_data'] = str(msg)

    def save_logs(self):
        now = datetime.datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")
        current_month_str = now.strftime("%Y-%m")

        log_file = os.path.join(self.log_dir, f"{current_date_str}_system_telemetry.json")
        history_file = os.path.join(self.log_dir, f"{current_date_str}_telemetry_history.jsonl")
        
        # Cleanup files from previous months
        try:
            for f_name in os.listdir(self.log_dir):
                if f_name.endswith('.json') or f_name.endswith('.jsonl'):
                    # Check if file has a date prefix but doesn't belong to the current month
                    if len(f_name) >= 7 and f_name[4] == '-' and f_name[7] == '-':
                        if not f_name.startswith(current_month_str):
                            os.remove(os.path.join(self.log_dir, f_name))
        except Exception as e:
            self.get_logger().error(f"Failed to cleanup old logs: {e}")
            

        output = {
            "timestamp": time.time(),
            "date_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "topics": {}
        }
        
        for topic, stats in self.topic_stats.items():
            if stats['timestamps']:
                output["topics"][topic] = {
                    'hz_fps': round(stats['hz_fps'], 2),
                    'last_received_sec_ago': round(time.time() - stats['timestamps'][-1], 3),
                    'data': stats['latest_data']
                }
            else:
                output["topics"][topic] = {
                    'hz_fps': 0.0,
                    'status': 'No data received yet'
                }
                
        try:
            # Save directly to MongoDB
            if hasattr(self, 'state_collection'):
                self.state_collection.replace_one({'_id': 'latest'}, {'_id': 'latest', **output}, upsert=True)
                self.history_collection.insert_one(output.copy())

            # Save latest state (overwrite) - Great for live monitoring tools
            with open(log_file, 'w') as f:
                json.dump(output, f, indent=2)
                
            # Save to history (append line) - Great for historical analysis
            with open(history_file, 'a') as f:
                f.write(json.dumps(output) + "\n")
                
        except Exception as e:
            self.get_logger().error(f"Failed to save log: {e}")

def main():
    rclpy.init()
    node = TopicLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
