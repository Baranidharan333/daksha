#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from rcl_interfaces.srv import SetParameters


class GravityScaleSetter(Node):

    def __init__(self):
        super().__init__("gravity_scale_setter")

        self.client = self.create_client(
            SetParameters,
            "/gravity_torque_node/set_parameters"
        )

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for gravity_torque_node...")

        default_scale = {
            "ff_scale.left_joint_1": 0.22,
            "ff_scale.left_joint_2": 0.22,
            "ff_scale.left_joint_3": 0.255,
            "ff_scale.left_joint_4": 0.35,
            "ff_scale.left_joint_5": 1.0,
            "ff_scale.left_joint_6": 1.0,
            "ff_scale.left_joint_7": 1.0,
            "ff_scale.right_joint_1": 0.22,
            "ff_scale.right_joint_2": 0.22,
            "ff_scale.right_joint_3": 0.255,
            "ff_scale.right_joint_4": 0.35,
            "ff_scale.right_joint_5": 1.0,
            "ff_scale.right_joint_6": 1.0,
            "ff_scale.right_joint_7": 1.0,
        }
        # default_scale = {
        #     "ff_scale.left_joint_1":  0.1,
        #     "ff_scale.left_joint_2":  0.1,
        #     "ff_scale.left_joint_3":  0.1,
        #     "ff_scale.left_joint_4":  0.1,
        #     "ff_scale.left_joint_5":  0.1,
        #     "ff_scale.left_joint_6":  0.1,
        #     "ff_scale.left_joint_7":  0.1,
        #     "ff_scale.right_joint_1": 0.1,
        #     "ff_scale.right_joint_2": 0.1,
        #     "ff_scale.right_joint_3": 0.1,
        #     "ff_scale.right_joint_4": 0.1,
        #     "ff_scale.right_joint_5": 0.1,
        #     "ff_scale.right_joint_6": 0.1,
        #     "ff_scale.right_joint_7": 0.1,
        # }
        # default_scale = {
        #     "ff_scale.left_joint_1":  0.215,
        #     "ff_scale.left_joint_2":  0.215,
        #     "ff_scale.left_joint_3":  0.30,
        #     "ff_scale.left_joint_4":  0.36,
        #     "ff_scale.left_joint_5":  1.32,
        #     "ff_scale.left_joint_6":  1.50,
        #     "ff_scale.left_joint_7":  2.00,

        #     "ff_scale.right_joint_1": 0.215,
        #     "ff_scale.right_joint_2": 0.215,
        #     "ff_scale.right_joint_3": 0.30,
        #     "ff_scale.right_joint_4": 0.36,
        #     "ff_scale.right_joint_5": 1.32,
        #     "ff_scale.right_joint_6": 1.50,
        #     "ff_scale.right_joint_7": 2.00,
        # }
        req = SetParameters.Request()

        for name, value in default_scale.items():
            p = Parameter()
            p.name = name
            p.value = ParameterValue(
                type=ParameterType.PARAMETER_DOUBLE,
                double_value=value,
            )
            req.parameters.append(p)

        future = self.client.call_async(req)

        rclpy.spin_until_future_complete(self, future)

        if future.result():
            self.get_logger().info("Updated ff_scale parameters.")
        else:
            self.get_logger().error("Failed to update parameters.")

        rclpy.shutdown()


def main():
    rclpy.init()
    GravityScaleSetter()


if __name__ == "__main__":
    main()
