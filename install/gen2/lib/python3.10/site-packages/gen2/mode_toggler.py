#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy, QoSHistoryPolicy

from rcl_interfaces.msg import (
    Parameter,
    ParameterType,
    ParameterValue,
    SetParametersResult,
)
from rcl_interfaces.srv import SetParameters

from sensor_msgs.msg import JointState
from std_msgs.msg import String


LEFT_JOINTS = [
    "left_joint_1",
    "left_joint_2",
    "left_joint_3",
    "left_joint_4",
    "left_joint_5",
    "left_joint_6",
    "left_joint_7",
]

RIGHT_JOINTS = [
    "right_joint_1",
    "right_joint_2",
    "right_joint_3",
    "right_joint_4",
    "right_joint_5",
    "right_joint_6",
    "right_joint_7",
]

# NOTE: deliberately excludes the grippers. In principle they should be
# verified too (teach_mode_node zeroes their gains same as the arm
# joints), but left/right_gripper_mit_controller currently fail to
# activate on this robot ("Not acceptable command interfaces combination"
# from resource_manager - the hardware interface isn't exporting gripper
# command interfaces), so /joint_states never carries gripper data. Adding
# them here made handle_verify() see permanently-missing data and get
# stuck reverting to TEACH every time. Re-add once the gripper controller
# activation failure (hw_interface / URDF <ros2_control> block) is fixed -
# see joint_cmd_publisher_from_joint_sates.py's matching GRIPPER_JOINTS,
# which has the same precondition.
ALL_JOINTS = LEFT_JOINTS + RIGHT_JOINTS

# States for the "exit teach mode" sequence.
STATE_TEACH = "TEACH"
STATE_NORMAL = "NORMAL"
STATE_CAPTURE_START = "CAPTURE_START"
STATE_WAIT_FOR_CAPTURE = "WAIT_FOR_CAPTURE"
STATE_VERIFY = "VERIFY"
STATE_EXIT_TEACH = "EXIT_TEACH"

# How long to wait for a downstream parameter-set (teach_mode_node /
# joint_cmd_publisher_from_joint_sates_node) to actually confirm before
# giving up. Both of those, in turn, wait on hardware gain-service calls,
# so this must comfortably exceed that inner timeout.
DOWNSTREAM_CONFIRM_TIMEOUT_S = 3.0

# Transient-local so a subscriber that connects after the last status
# change (e.g. mode_toggler was already sitting in "teach" at startup
# before an operator's node subscribes) still gets that last value
# instead of waiting forever for a transition that may never happen.
STATUS_QOS = QoSProfile(
    depth=1,
    reliability=QoSReliabilityPolicy.RELIABLE,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
    history=QoSHistoryPolicy.KEEP_LAST,
)


class ModeToggler(Node):

    def __init__(self):

        super().__init__("mode_toggler")

        self.declare_parameter("mode", "teach")

        self.declare_parameter("capture_duration_sec", 1.0)
        self.declare_parameter("position_tolerance_rad", 0.0349066)
        self.declare_parameter("max_retries", 3)

        self.capture_duration = self.get_parameter(
            "capture_duration_sec"
        ).value

        self.tolerance = self.get_parameter(
            "position_tolerance_rad"
        ).value

        self.max_retries = self.get_parameter(
            "max_retries"
        ).value

        self.mode = self.get_parameter("mode").value

        if self.mode not in ("teach", "normal"):
            self.get_logger().warn(
                f"Invalid initial mode '{self.mode}', defaulting to 'teach'"
            )
            self.mode = "teach"

        # -------- Parameter clients --------
        # These live on their own reentrant callback group so
        # set_teach_mode()/set_publish_joint_cmd() can block waiting on
        # their responses without deadlocking the (default-group)
        # parameter callback / state-machine timer that call them. This
        # only works because main() spins with a MultiThreadedExecutor.

        self._client_cb_group = ReentrantCallbackGroup()

        self.teach_client = self.create_client(
            SetParameters,
            "/teach_mode_node/set_parameters",
            callback_group=self._client_cb_group,
        )

        self.publish_cmd_client = self.create_client(
            SetParameters,
            "/joint_cmd_publisher_from_joint_sates_node/set_parameters",
            callback_group=self._client_cb_group,
        )

        self.get_logger().info(
            "Waiting for teach_mode_node and "
            "joint_cmd_publisher_from_joint_sates_node..."
        )

        self.teach_client.wait_for_service()
        self.publish_cmd_client.wait_for_service()

        self.get_logger().info("Downstream parameter services connected.")

        # -------- Status topic --------
        # The only trustworthy "has the mode switch actually landed on
        # hardware" signal. The "mode" *parameter* can't serve this
        # purpose: ROS auto-accepts a parameter's new value as soon as
        # the on-set callback returns successful=True, regardless of
        # what this class does internally, so external pollers of
        # `ros2 param get mode_toggler mode` would always see the
        # requested value instantly, not the settled one.

        self.status_pub = self.create_publisher(
            String, "/mode_toggler/status", STATUS_QOS
        )

        # -------- State --------

        self.state = STATE_TEACH if self.mode == "teach" else STATE_NORMAL
        self.retry_count = 0
        self.capture_start_time = None

        self.latest_ramped_cmd = {}
        self.latest_joint_states = {}

        # -------- Subscriptions --------

        # /joint_cmd is the raw, unramped target - during capture it's just
        # joint_cmd_publisher_from_joint_sates_node echoing /joint_states
        # back, so comparing it to /joint_states in handle_verify() would be
        # a tautology (always passes instantly). /jnt_cmt_to_ctrl carries
        # joint_command_limiter's actual velocity/acceleration-ramped
        # current_pos - the value that will really drive the stiff
        # controller once gains are restored - so that's what needs to
        # match /joint_states before it's safe to exit teach mode.
        self.create_subscription(
            JointState,
            "/jnt_cmt_to_ctrl",
            self.ramped_cmd_callback,
            10
        )

        self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_states_callback,
            10
        )

        # -------- Parameter callback + state machine timer --------

        self.add_on_set_parameters_callback(self.parameter_callback)

        self.create_timer(0.05, self.tick)

        # Apply initial mode. Fire-and-forget here on purpose: the
        # executor isn't spinning yet at this point in __init__ (main()
        # only starts it after construction), so a blocking wait on
        # set_teach_mode()/set_publish_joint_cmd() would never see its
        # future complete and would just time out. teach_mode_node
        # applies its own startup gains independently anyway.
        if self.mode == "teach":
            self._fire_and_forget_teach_mode(True)
        else:
            self._fire_and_forget_publish_cmd(False)

        self._publish_status(self.mode)

    ############################################################
    # Subscriptions
    ############################################################

    def ramped_cmd_callback(self, msg):
        for name, position in zip(msg.name, msg.position):
            self.latest_ramped_cmd[name] = position

    def joint_states_callback(self, msg):
        for name, position in zip(msg.name, msg.position):
            self.latest_joint_states[name] = position

    ############################################################
    # Status
    ############################################################

    def _publish_status(self, status):
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)

    ############################################################
    # Parameter service calls
    ############################################################

    def _fire_and_forget_teach_mode(self, enabled):
        req = SetParameters.Request()
        p = Parameter()
        p.name = "teach_mode"
        p.value = ParameterValue(
            type=ParameterType.PARAMETER_BOOL,
            bool_value=enabled,
        )
        req.parameters.append(p)
        self.teach_client.call_async(req)

    def _fire_and_forget_publish_cmd(self, enabled):
        req = SetParameters.Request()
        p = Parameter()
        p.name = "publish_joint_cmd"
        p.value = ParameterValue(
            type=ParameterType.PARAMETER_BOOL,
            bool_value=enabled,
        )
        req.parameters.append(p)
        self.publish_cmd_client.call_async(req)

    def _wait_confirm(self, future, what):
        """Blocks (bounded) until a downstream SetParameters call actually
        confirms, returning True only if it truly succeeded. Relies on
        the client living in a reentrant group separate from whatever
        callback is calling this, under a MultiThreadedExecutor."""

        deadline = time.monotonic() + DOWNSTREAM_CONFIRM_TIMEOUT_S

        while not future.done() and time.monotonic() < deadline:
            time.sleep(0.005)

        if not future.done():
            self.get_logger().error(f"{what}: downstream confirmation timed out")
            return False

        result = future.result()

        if result is None or not result.results:
            self.get_logger().error(f"{what}: downstream call returned no result")
            return False

        if not all(r.successful for r in result.results):
            self.get_logger().error(f"{what}: downstream call rejected the change")
            return False

        return True

    def set_teach_mode(self, enabled):

        req = SetParameters.Request()

        p = Parameter()
        p.name = "teach_mode"
        p.value = ParameterValue(
            type=ParameterType.PARAMETER_BOOL,
            bool_value=enabled,
        )
        req.parameters.append(p)

        self.get_logger().info(f"Requesting teach_mode = {enabled}")

        future = self.teach_client.call_async(req)

        return self._wait_confirm(future, f"teach_mode={enabled}")

    def set_publish_joint_cmd(self, enabled):

        req = SetParameters.Request()

        p = Parameter()
        p.name = "publish_joint_cmd"
        p.value = ParameterValue(
            type=ParameterType.PARAMETER_BOOL,
            bool_value=enabled,
        )
        req.parameters.append(p)

        self.get_logger().info(f"Requesting publish_joint_cmd = {enabled}")

        future = self.publish_cmd_client.call_async(req)

        return self._wait_confirm(future, f"publish_joint_cmd={enabled}")

    ############################################################
    # Parameter callback (validation + trigger only)
    ############################################################

    def parameter_callback(self, params):

        result = SetParametersResult()
        result.successful = True

        for param in params:

            if param.name != "mode":
                continue

            new_mode = param.value

            if new_mode not in ("teach", "normal"):
                result.successful = False
                result.reason = "mode must be 'teach' or 'normal'"
                return result

            # Gate on the real settled state, not self.mode: self.mode is
            # only updated once a transition is confirmed, so gating on
            # it too would silently swallow a retry after a failed
            # attempt (self.mode would still say the old value even
            # though nothing actually happened).
            if new_mode == "teach" and self.state == STATE_TEACH:
                continue
            if new_mode == "normal" and self.state == STATE_NORMAL:
                continue

            if new_mode == "teach":
                self.enter_teach_mode()
            else:
                self.start_exit_teach_sequence()

        return result

    ############################################################
    # Mode transitions
    ############################################################

    def enter_teach_mode(self):

        self.get_logger().info(
            "========== ENTERING TEACH MODE =========="
        )

        self.retry_count = 0
        self.capture_start_time = None

        self._publish_status("transitioning")

        ok = self.set_teach_mode(True)

        if not ok:
            self.get_logger().error(
                "Failed to confirm teach-mode gains on hardware; "
                "not switching state."
            )
            return

        self.mode = "teach"
        self.state = STATE_TEACH

        self._publish_status("teach")

    def start_exit_teach_sequence(self):

        if self.state not in (STATE_TEACH, STATE_NORMAL):
            self.get_logger().warn(
                "Exit-teach sequence already in progress, ignoring request."
            )
            return

        self.get_logger().info(
            "========== EXITING TEACH MODE =========="
        )

        self.retry_count = 0

        self._publish_status("transitioning")

        self.state = STATE_CAPTURE_START

    ############################################################
    # State machine
    ############################################################

    def tick(self):

        if self.state == STATE_CAPTURE_START:
            self.handle_capture_start()
        elif self.state == STATE_WAIT_FOR_CAPTURE:
            self.handle_wait_for_capture()
        elif self.state == STATE_VERIFY:
            self.handle_verify()
        elif self.state == STATE_EXIT_TEACH:
            self.handle_exit_teach()
        # STATE_TEACH / STATE_NORMAL: nothing to do.

    def handle_capture_start(self):

        self.set_publish_joint_cmd(True)

        self.capture_start_time = self.get_clock().now()

        self.state = STATE_WAIT_FOR_CAPTURE

    def handle_wait_for_capture(self):

        elapsed = (
            self.get_clock().now() - self.capture_start_time
        ).nanoseconds / 1e9

        if elapsed >= self.capture_duration:
            self.state = STATE_VERIFY

    def handle_verify(self):

        if not self.latest_ramped_cmd or not self.latest_joint_states:
            self.get_logger().warn(
                "No ramped-cmd / joint_states data yet, waiting..."
            )
            self.capture_start_time = self.get_clock().now()
            self.state = STATE_WAIT_FOR_CAPTURE
            return

        all_ok = True

        for name in ALL_JOINTS:

            cmd_pos = self.latest_ramped_cmd.get(name)
            state_pos = self.latest_joint_states.get(name)

            if cmd_pos is None or state_pos is None:
                self.get_logger().warn(f"Missing data for joint '{name}'")
                all_ok = False
                continue

            error = abs(cmd_pos - state_pos)

            if error >= self.tolerance:
                all_ok = False
                self.get_logger().warn(
                    f"{name}: cmd={cmd_pos:.4f} state={state_pos:.4f} "
                    f"error={error:.4f} rad (tolerance={self.tolerance:.4f})"
                )

        if all_ok:
            self.state = STATE_EXIT_TEACH
            return

        self.retry_count += 1

        if self.retry_count > self.max_retries:
            self.get_logger().error(
                f"Failed to converge after {self.max_retries} retries. "
                "Aborting exit-teach sequence, staying in TEACH mode."
            )

            self.set_publish_joint_cmd(False)
            ok = self.set_teach_mode(True)

            self.mode = "teach"
            self.state = STATE_TEACH

            if ok:
                self._publish_status("teach")
            else:
                self.get_logger().error(
                    "Also failed to confirm teach-mode gains while aborting "
                    "the exit-teach sequence; arm gain state is uncertain."
                )
            return

        self.get_logger().warn(
            f"Verification failed, retrying "
            f"({self.retry_count}/{self.max_retries})..."
        )

        self.state = STATE_CAPTURE_START

    def handle_exit_teach(self):

        cmd_ok = self.set_publish_joint_cmd(False)
        gains_ok = self.set_teach_mode(False)

        if not (cmd_ok and gains_ok):
            self.get_logger().error(
                "Failed to confirm normal-mode gains on hardware; "
                "reverting to TEACH mode for safety."
            )

            self.set_teach_mode(True)

            self.mode = "teach"
            self.state = STATE_TEACH

            self._publish_status("teach")
            return

        self.mode = "normal"
        self.state = STATE_NORMAL

        self._publish_status("normal")

        self.get_logger().info(
            "========== NORMAL MODE ACTIVE =========="
        )


def main(args=None):

    rclpy.init(args=args)

    node = ModeToggler()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()
