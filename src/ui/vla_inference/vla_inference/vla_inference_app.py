#!/usr/bin/env python3
"""VLA inference command console.

Serves a web page where an operator types a task in plain English and
publishes it as a std_msgs/String for the vision-language-action engine to
execute. Also publishes a 'stop' on the same topic for the halt button.

Was daksha_ui/daksha_ui/subui_app.py; split into its own package so the
inference console ships independently of the robot dashboard.
"""

import logging
import threading
from flask import Flask, request, jsonify, render_template
import rclpy
from rclpy.exceptions import ParameterNotDeclaredException
from rclpy.node import Node
from std_msgs.msg import String

logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)

class InstructionPublisher(Node):
    def __init__(self):
        # Settings come from Clients_UI/config/vla_inference.yaml, passed as a ROS
        # parameter file by launch/vla_inference.launch.py. Declaring from
        # overrides means a key added to that file is readable here with no
        # change to this script.
        super().__init__(
            'ui_instruction_publisher',
            automatically_declare_parameters_from_overrides=True,
        )

        self.host = self.param('vla_inference.host', '0.0.0.0')
        self.port = int(self.param('vla_inference.port', 7001))
        topic = self.param('vla_inference.instruction_topic', '/viveka_instruction')

        self.publisher_ = self.create_publisher(String, topic, 10)
        self.get_logger().info(f'Publishing instructions on {topic}, serving on {self.host}:{self.port}')

    def param(self, name, default):
        """Parameter value, or `default` when no params file supplied it.

        automatically_declare_parameters_from_overrides only declares what was
        actually passed in, so a node run without --params-file has nothing
        declared and every lookup has to fall back.
        """
        try:
            return self.get_parameter(name).value
        except ParameterNotDeclaredException:
            return default

    def publish_instruction(self, instruction_text):
        msg = String()
        msg.data = instruction_text
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing instruction: "{msg.data}"')

ros_node = None

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

def main():
    global ros_node

    # The node is built here, not on the background thread, because its
    # parameters carry the host/port Flask binds to - the old version slept a
    # second and hoped the thread had got there first.
    rclpy.init(args=None)
    ros_node = InstructionPublisher()

    threading.Thread(target=rclpy.spin, args=(ros_node,), daemon=True).start()

    try:
        app.run(host=ros_node.host, port=ros_node.port, debug=False)
    finally:
        ros_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
