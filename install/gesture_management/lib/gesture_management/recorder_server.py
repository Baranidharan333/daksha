#!/usr/bin/env python3
import os
import rclpy
import pandas as pd

from rclpy.node import Node
from sensor_msgs.msg import JointState

from gesture_management.srv import StartRecording

from ament_index_python.packages import get_package_share_directory


class RecorderServer(Node):

    def __init__(self):
        super().__init__('recorder_server')

        self.subscription = None
        self.records = []
        self.recording_name = None

        # Recordings dir defaults to <package>/recordings (resolved at runtime,
        # no hardcoded home path), same as gesture_management_app.py and
        # replay_server.py. Override with:
        #   ros2 run gesture_management recorder_server.py \
        #        --ros-args -p recordings_dir:=/abs/path/to/recordings
        # or the GESTURE_RECORDINGS_DIR env var.
        default_dir = os.environ.get(
            "GESTURE_RECORDINGS_DIR",
            os.path.join(
                get_package_share_directory('gesture_management'),
                'recordings',
            ),
        )
        self.declare_parameter('recordings_dir', default_dir)

        self.recording_srv = self.create_service(
            StartRecording,
            'recording',
            self.recording_callback
        )

    def _recordings_dir(self):
        return self.get_parameter('recordings_dir').get_parameter_value().string_value

    def recording_callback(self, request, response):
        if request.action == 'start':
            if self.subscription:
                self.destroy_subscription(self.subscription)
            self.records = []
            self.recording_name = request.recording_name
            self.topic_name = request.topic_name

            self.subscription = self.create_subscription(
                JointState,
                request.topic_name,
                self.joint_callback,
                10
            )

            response.success = True
            response.message = 'Recording started'

        elif request.action == 'stop':

            if not self.records:
                response.success = False
                response.message = 'No records to save'
                return response

            record_dir = self._recordings_dir()
            os.makedirs(record_dir, exist_ok=True)

            file_path = os.path.join(record_dir, f"{self.recording_name}.parquet")

            df = pd.DataFrame(self.records)

            # IMPORTANT: ensure proper parquet engine
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')

            # cleanup subscription
            if self.subscription:
                self.destroy_subscription(self.subscription)
                self.subscription = None

            response.success = True
            response.message = f'Saved to {file_path}'

        else:
            response.success = False
            response.message = f'Invalid action: {request.action}'

        return response

    def joint_callback(self, msg):

        timestamp_ns = (
            msg.header.stamp.sec * 1000000000 +
            msg.header.stamp.nanosec
        )

        for i, joint_name in enumerate(msg.name):

            position = msg.position[i] if i < len(msg.position) else 0.0
            velocity = msg.velocity[i] if i < len(msg.velocity) else 0.0
            effort = msg.effort[i] if i < len(msg.effort) else 0.0

            self.records.append({
                'timestamp_ns': timestamp_ns,
                'source_topic': self.topic_name,
                'joint_name': joint_name,
                'position': position,
                'velocity': velocity,
                'effort': effort
            })


def main(args=None):
    rclpy.init(args=args)
    node = RecorderServer()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
