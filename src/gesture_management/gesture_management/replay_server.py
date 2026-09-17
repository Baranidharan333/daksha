#!/usr/bin/env python3
import time
import os
import pandas as pd
import rclpy

from rclpy.node import Node
from sensor_msgs.msg import JointState

from gesture_management.srv import ReplayRecording

from ament_index_python.packages import get_package_share_directory


class ReplayServer(Node):

    def __init__(self):
        super().__init__('replay_server')

        # Recordings dir defaults to <package>/recordings (resolved at runtime,
        # no hardcoded home path). Override with:
        #   ros2 run gesture_management replay_server.py \
        #        --ros-args -p recordings_dir:=/abs/path/to/recordings
        default_dir = os.environ.get(
            "GESTURE_RECORDINGS_DIR",
            os.path.join(
                get_package_share_directory('gesture_management'),
                'recordings'
            )
        )
        self.declare_parameter('recordings_dir', default_dir)

        self.srv = self.create_service(
            ReplayRecording,
            'replay_recording',
            self.replay_callback
        )

    def _recordings_dir(self):
        return self.get_parameter('recordings_dir').get_parameter_value().string_value

    def replay_callback(self, request, response):

        record_dir = self._recordings_dir()
        file_path = os.path.join(record_dir, f"{request.recording_name}.parquet")

        try:
            df = pd.read_parquet(file_path)
        except Exception as e:
            response.success = False
            response.message = f'Failed to read {file_path}: {str(e)}'
            return response

        pub = self.create_publisher(
            JointState,
            request.output_topic,
            10
        )

        grouped = df.groupby('timestamp_ns')

        previous_time = None

        for timestamp_ns, group in grouped:

            if previous_time is not None:

                delay = (
                    (timestamp_ns - previous_time)
                    / 1e9
                    / request.replay_speed
                )

                time.sleep(delay)

            msg = JointState()

            msg.header.stamp.sec = int(timestamp_ns // 1e9)
            msg.header.stamp.nanosec = int(timestamp_ns % 1e9)

            msg.name = group['joint_name'].tolist()
            msg.position = group['position'].tolist()
            msg.velocity = group['velocity'].tolist()
            msg.effort = group['effort'].tolist()

            pub.publish(msg)

            previous_time = timestamp_ns

        response.success = True
        response.message = 'Replay completed'

        return response


def main(args=None):
    rclpy.init(args=args)
    node = ReplayServer()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
