#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import time
import numpy as np
import threading
import argparse
import sys

class Ros2LatencyMeasurer(Node):
    def __init__(self, topic, joint_names, delta=0.01, joint_index=0, check_field='position', iterations=50, ping_interval=1.0):
        super().__init__('ros2_latency_measurer')

        self.topic = topic
        self.joint_names = joint_names
        self.delta = delta
        self.joint_index = joint_index
        self.check_field = check_field  # 'position', 'velocity', or 'effort'
        self.iterations = iterations
        self.ping_interval = ping_interval

        self.publisher = self.create_publisher(JointTrajectory, self.topic, 1)
        self.subscriber = self.create_subscription(JointState, '/joint_states', self.state_callback, 1)

        self.current_state = None
        self.cmd_time = None
        self.waiting_for_response = False
        self.baseline_val = None

        self.latencies = []
        self.current_iter = 0
        self.direction = 1.0

        self.timer = self.create_timer(self.ping_interval, self.ping)
        self.lock = threading.Lock()

        self.get_logger().info(f"Started ROS2 Latency Measurer.")
        self.get_logger().info(f"Publishing JointTrajectory on '{self.topic}' with joint names {self.joint_names}.")
        self.get_logger().info(f"Targeting joint index {self.joint_index} with a delta of {self.delta} on field '{self.check_field}'.")
        self.get_logger().info(f"Total iterations: {self.iterations}, ping interval: {self.ping_interval}s")

    def get_field_dict(self, msg):
        if self.check_field == 'position':
            values = msg.position
        elif self.check_field == 'velocity':
            values = msg.velocity
        elif self.check_field == 'effort':
            values = msg.effort
        else:
            values = msg.position
        return dict(zip(msg.name, values))

    def state_callback(self, msg):
        with self.lock:
            self.current_state = msg

            if self.waiting_for_response and self.baseline_val is not None:
                values = self.get_field_dict(msg)
                target_name = self.joint_names[self.joint_index]
                if target_name not in values:
                    return

                current_val = values[target_name]

                # Check if the value has moved significantly toward the target delta
                # We consider a 10% movement of the delta as a response
                threshold = self.baseline_val + (self.delta * 0.1 * self.active_direction)

                responded = False
                if self.active_direction > 0 and current_val >= threshold:
                    responded = True
                elif self.active_direction < 0 and current_val <= threshold:
                    responded = True

                if responded:
                    latency = time.perf_counter() - self.cmd_time
                    self.latencies.append(latency * 1000.0)
                    self.get_logger().info(f'Iteration {self.current_iter}/{self.iterations}: Latency {latency*1000.0:.2f} ms (moved from {self.baseline_val:.4f} to {current_val:.4f})')
                    self.waiting_for_response = False

    def ping(self):
        with self.lock:
            if self.current_iter >= self.iterations:
                self.print_results()
                self.timer.cancel()
                rclpy.shutdown()
                return

            if self.current_state is None:
                self.get_logger().info('Waiting for /joint_states...')
                return

            if self.waiting_for_response:
                self.get_logger().warn('Timeout waiting for response on last ping.')

            values = self.get_field_dict(self.current_state)
            missing = [name for name in self.joint_names if name not in values]
            if missing:
                self.get_logger().error(f"Cannot read field '{self.check_field}' for joint(s) {missing} in /joint_states")
                return

            baseline_vals = [values[name] for name in self.joint_names]
            self.baseline_val = baseline_vals[self.joint_index]

            new_positions = list(baseline_vals)
            new_positions[self.joint_index] = float(self.baseline_val + (self.delta * self.direction))

            traj_msg = JointTrajectory()
            traj_msg.joint_names = self.joint_names

            point = JointTrajectoryPoint()
            point.positions = new_positions
            point.time_from_start = Duration(sec=0, nanosec=0)
            traj_msg.points.append(point)

            self.waiting_for_response = True
            self.cmd_time = time.perf_counter()
            self.active_direction = self.direction
            self.publisher.publish(traj_msg)

            self.direction *= -1.0
            self.current_iter += 1

    def print_results(self):
        if self.latencies:
            self.get_logger().info('\n' + '='*40)
            self.get_logger().info(f'Results over {len(self.latencies)} successful pings:')
            self.get_logger().info(f'  Mean Latency: {np.mean(self.latencies):.2f} ms')
            self.get_logger().info(f'  Min Latency:  {np.min(self.latencies):.2f} ms')
            self.get_logger().info(f'  Max Latency:  {np.max(self.latencies):.2f} ms')
            self.get_logger().info(f'  Std Dev:      {np.std(self.latencies):.2f} ms')
            self.get_logger().info('='*40 + '\n')
        else:
            self.get_logger().warn('No responses received during the test!')

DEFAULT_JOINT_NAMES = [
    "left_joint_1",
    "left_joint_2",
    "left_joint_3",
    "left_joint_4",
    "left_joint_5",
    "left_joint_6",
    "left_joint_7",
]

def main():
    parser = argparse.ArgumentParser(description='Measure ROS2 Control Loop Latency via JointTrajectory commands')
    parser.add_argument('--topic', type=str, default='/left_arm_mit_controller/joint_trajectory',
                        help='JointTrajectory topic to publish commands on (default: /left_arm_mit_controller/joint_trajectory)')
    parser.add_argument('--joint_names', type=str, default=','.join(DEFAULT_JOINT_NAMES),
                        help='Comma-separated joint names, in the order expected by --topic (default: left arm joints)')
    parser.add_argument('--delta', type=float, default=0.01, help='Deviation to apply to the command (default: 0.01)')
    parser.add_argument('--joint_index', type=int, default=0, help='Index within --joint_names of the joint to actuate (default: 0)')
    parser.add_argument('--field', type=str, default='position', choices=['position', 'velocity', 'effort'],
                        help='Field to monitor in /joint_states and base commands on (default: position)')
    parser.add_argument('--iterations', type=int, default=50, help='Number of pings (default: 50)')
    parser.add_argument('--interval', type=float, default=1.0, help='Ping interval in seconds (default: 1.0)')

    # ROS2 args are passed before script args usually, so we parse known args to avoid errors
    args, unknown = parser.parse_known_args()

    rclpy.init(args=sys.argv)

    joint_names = [name.strip() for name in args.joint_names.split(',') if name.strip()]
    if not (0 <= args.joint_index < len(joint_names)):
        print(f"--joint_index {args.joint_index} is out of range for {len(joint_names)} joint names", file=sys.stderr)
        sys.exit(1)

    measurer = Ros2LatencyMeasurer(
        topic=args.topic,
        joint_names=joint_names,
        delta=args.delta,
        joint_index=args.joint_index,
        check_field=args.field,
        iterations=args.iterations,
        ping_interval=args.interval
    )

    try:
        rclpy.spin(measurer)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        measurer.get_logger().error(f"Error: {e}")
    finally:
        measurer.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
