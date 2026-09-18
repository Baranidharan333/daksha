#!/usr/bin/env python3

import csv
import datetime
import os

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState


class TopicCsvLogger:
    """Opens one timestamped CSV file for a single topic and appends one row
    per joint on every JointState message received."""

    def __init__(self, log_dir: str, topic_name: str, run_stamp: str):
        safe_name = topic_name.strip("/").replace("/", "_")
        self.path = os.path.join(log_dir, f"{safe_name}_{run_stamp}.csv")

        self._file = open(self.path, "w", newline="")
        self._writer = csv.writer(self._file)
        self._writer.writerow(
            ["stamp_iso", "ros_time_sec", "joint_name", "position", "velocity", "effort"]
        )

    def log(self, message: JointState) -> None:
        stamp_iso = datetime.datetime.now().isoformat(timespec="milliseconds")
        ros_time_sec = message.header.stamp.sec + message.header.stamp.nanosec * 1e-9

        names = list(message.name)
        positions = list(message.position)
        velocities = list(message.velocity)
        efforts = list(message.effort)

        for i, name in enumerate(names):
            self._writer.writerow([
                stamp_iso,
                ros_time_sec,
                name,
                positions[i] if i < len(positions) else "",
                velocities[i] if i < len(velocities) else "",
                efforts[i] if i < len(efforts) else "",
            ])
        self._file.flush()

    def close(self) -> None:
        self._file.close()


class JointCmdLogger(Node):

    def __init__(self):
        super().__init__("joint_cmd_logger")

        self.declare_parameter("log_dir", os.path.expanduser("~/.ros/joint_cmd_logger_logs"))
        log_dir = self.get_parameter("log_dir").get_parameter_value().string_value
        os.makedirs(log_dir, exist_ok=True)

        run_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        self._joint_cmd_logger = TopicCsvLogger(log_dir, "/joint_cmd", run_stamp)
        self._jnt_cmt_to_ctrl_logger = TopicCsvLogger(log_dir, "/jnt_cmt_to_ctrl", run_stamp)

        self.create_subscription(
            JointState, "/joint_cmd", self._joint_cmd_logger.log, qos_profile_sensor_data
        )
        self.create_subscription(
            JointState, "/jnt_cmt_to_ctrl", self._jnt_cmt_to_ctrl_logger.log, qos_profile_sensor_data
        )

        print("JOINT CMD LOGGER STARTED")
        print(f"  /joint_cmd        -> {self._joint_cmd_logger.path}")
        print(f"  /jnt_cmt_to_ctrl  -> {self._jnt_cmt_to_ctrl_logger.path}")

    def destroy_node(self):
        self._joint_cmd_logger.close()
        self._jnt_cmt_to_ctrl_logger.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = JointCmdLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
