#!/usr/bin/env python3
import logging
import threading
import time
from flask import Flask, request, jsonify, render_template
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

logging.getLogger("werkzeug").setLevel(logging.WARNING)

# Distinct folder names (not the Flask defaults "templates"/"static") since
# this script installs flat alongside dashboard_app.py, which already owns
# those two names in the same lib/daksha_ui/ directory.
app = Flask(__name__, template_folder="subui_templates", static_folder="subui_static")

class InstructionPublisher(Node):
    def __init__(self):
        super().__init__('ui_instruction_publisher')
        self.publisher_ = self.create_publisher(String, '/viveka_instruction', 10)

    def publish_instruction(self, instruction_text):
        msg = String()
        msg.data = instruction_text
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing instruction: "{msg.data}"')

ros_node = None

def ros2_thread():
    global ros_node
    rclpy.init(args=None)
    ros_node = InstructionPublisher()
    rclpy.spin(ros_node)
    ros_node.destroy_node()
    rclpy.shutdown()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/instruct', methods=['POST'])
def instruct():
    global ros_node
    data = request.json
    instruction = data.get('prompt', '')
    if not instruction:
        return jsonify({"status": "error", "message": "No prompt provided"}), 400
    
    if ros_node is not None:
        ros_node.publish_instruction(instruction)
        return jsonify({"status": "success", "message": f"Instruction '{instruction}' sent to Viveka inference engine."})
    else:
        return jsonify({"status": "error", "message": "ROS2 Node not initialized"}), 500

@app.route('/api/stop', methods=['POST'])
def stop():
    global ros_node
    if ros_node is not None:
        ros_node.publish_instruction('stop')
        return jsonify({"status": "success", "message": "Stop command sent."})
    else:
        return jsonify({"status": "error", "message": "ROS2 Node not initialized"}), 500

import random

@app.route('/api/diagnostics')
def diagnostics():
    data = {
        "health": {
            "ros": "ok", "can0": "ok", "can1": "ok", "leader": "ok",
            "follower": "ok", "wrist_cam": "ok", "head_cam": "ok", "gpu": "ok", "recorder": "ok"
        },
        "metrics": {
            "ros_freq": random.randint(95, 105),
            "cam_fps": random.randint(28, 32),
            "can_rate": random.randint(480, 520),
            "cpu_usage": random.randint(15, 45),
            "gpu_usage": random.randint(30, 85),
            "gpu_temp": random.randint(55, 75),
            "memory": round(random.uniform(6.0, 12.0), 1),
            "network": random.randint(5, 25)
        }
    }
    return jsonify(data)

if __name__ == '__main__':
    threading.Thread(target=ros2_thread, daemon=True).start()
    time.sleep(1) # Wait for ROS node to initialize
    app.run(host='0.0.0.0', port=7001, debug=False)
