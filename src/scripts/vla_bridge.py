#!/usr/bin/env python3

import rclpy

from rclpy.node import Node

from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger

from collections import deque

import numpy as np


# MEDIAN_WINDOW = 3
# MAX_JUMP = 0.03
# MAX_VEL = 0.5
# LOW_PASS_ALPHA = 0.15
# DEADBAND = 0.01
# DEFAULT_DT = 1.0 / 10.0

MEDIAN_WINDOW = 1
MAX_JUMP = 0.8
MAX_VEL = 0.8
LOW_PASS_ALPHA = 0.15
DEADBAND = 0.01
DEFAULT_DT = 1.0 / 30.0
# MEDIAN_WINDOW = 3

# MAX_JUMP = 0.20

# MAX_VEL = 2.0

# LOW_PASS_ALPHA = 0.20

# DEADBAND = 0.003

# DEFAULT_DT = 1.0 / 30.0

# MEDIAN_WINDOW = 3

# MAX_JUMP = 0.20

# MAX_VEL = 4.0

# LOW_PASS_ALPHA = 0.30

# DEADBAND = 0.0

# DEFAULT_DT = 1.0 / 10.0


class JointCommandFilter(Node):

    def __init__(self):
        super().__init__("joint_command_filter")

        self.right_locked = False
        self.left_locked = False

        self.right_state = None
        self.left_state = None
        self.filtered_position = None
        self.prediction_history = deque(maxlen=MEDIAN_WINDOW)
        self.last_predict_time = None

        self.create_subscription(
            JointState,
            "/RightArmSystem_ordered_joint_states",
            self.right_state_cb,
            10
        )

        self.create_subscription(
            JointState,
            "/LeftArmSystem_ordered_joint_states",
            self.left_state_cb,
            10
        )

        self.create_subscription(
            JointState,
            "/joint_cmd_predict",
            self.predict_cb,
            10
        )

        self.create_service(
            Trigger,
            "/right_arm_trigger_handler",
            self.right_trigger_cb
        )

        self.create_service(
            Trigger,
            "/left_arm_trigger_handler",
            self.left_trigger_cb
        )

        self.pub = self.create_publisher(
            JointState,
            "/joint_cmd",
            10
        )

    def right_state_cb(self, msg):
        self.right_state = msg

    def left_state_cb(self, msg):
        self.left_state = msg

    def right_trigger_cb(self, request, response):
        self.right_locked = not self.right_locked
        state = "LOCKED" if self.right_locked else "UNLOCKED"
        self.get_logger().info(f"RIGHT ARM {state}")
        response.success = True
        response.message = f"RIGHT ARM {state}"
        return response

    def left_trigger_cb(self, request, response):
        self.left_locked = not self.left_locked
        state = "LOCKED" if self.left_locked else "UNLOCKED"
        self.get_logger().info(f"LEFT ARM {state}")
        response.success = True
        response.message = f"LEFT ARM {state}"
        return response

    def predict_cb(self, msg):

        if self.right_state is None or self.left_state is None:
            return

        predicted = np.array(msg.position, dtype=float)
        current = np.array(
            list(self.right_state.position)
            + list(self.left_state.position),
            dtype=float
        )

        if predicted.size == 0 or current.size == 0:
            return

        joint_count = min(predicted.size, current.size)
        predicted = predicted[:joint_count]
        current = current[:joint_count]

        if self.filtered_position is None or self.filtered_position.size != joint_count:
            self.filtered_position = current.copy()
            self.prediction_history.clear()

        now = self.get_clock().now()
        dt = DEFAULT_DT
        if self.last_predict_time is not None:
            measured_dt = (now - self.last_predict_time).nanoseconds * 1e-9
            if measured_dt > 0.0:
                dt = measured_dt
        self.last_predict_time = now

        self.prediction_history.append(predicted.copy())

        if len(self.prediction_history) >= MEDIAN_WINDOW:
            predicted = np.median(
                np.array(self.prediction_history),
                axis=0
            )

        predicted = self.limit_jump(predicted)
        predicted = self.limit_velocity(predicted, dt)
        predicted = self.apply_deadband(predicted)
        filtered = (
            LOW_PASS_ALPHA * predicted
            + (1.0 - LOW_PASS_ALPHA) * self.filtered_position
        )

        out = JointState()

        out.header = msg.header
        out.name = msg.name

        if self.right_locked:

            for i in range(min(8, joint_count)):
                filtered[i] = current[i]

        if self.left_locked:

            for i in range(8, min(16, joint_count)):
                filtered[i] = current[i]

        self.filtered_position = filtered.copy()
        out.position = filtered.tolist()

        if self.right_locked and self.left_locked:
            return

        self.pub.publish(out)

    def limit_jump(self, predicted):
        diff = predicted - self.filtered_position
        return self.filtered_position + np.clip(diff, -MAX_JUMP, MAX_JUMP)

    def limit_velocity(self, predicted, dt):
        max_step = MAX_VEL * dt
        delta = predicted - self.filtered_position
        return self.filtered_position + np.clip(delta, -max_step, max_step)

    def apply_deadband(self, predicted):
        delta = predicted - self.filtered_position
        deadband_mask = np.abs(delta) < DEADBAND
        predicted[deadband_mask] = self.filtered_position[deadband_mask]
        return predicted


def main():
    rclpy.init()

    node = JointCommandFilter()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
