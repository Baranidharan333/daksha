#!/usr/bin/env python3
"""
joint_cmd_state_delay.py
-------------------------
Passively measures the reaction time between /joint_cmd (the commanded
target position) and /joint_states (the actual reported position),
per joint.

How it works, per joint:
  1. Watch /joint_cmd. When a joint's commanded position jumps by more
     than --threshold rad since the last commanded value, and no
     measurement is already pending for that joint, start a timer
     (t0 = time the command was received) and remember the new target.
     If the command keeps moving before it's resolved, the target is
     updated but t0 is kept, so the measured delay is to the final
     resting value of that motion.
  2. Watch /joint_states. Once a pending joint's actual position comes
     within --tolerance rad of the target, record latency = now - t0.
  3. A pending measurement is dropped (not counted) if it doesn't
     resolve within --timeout seconds.

This captures the whole path: DDS transport -> joint_command_limiter's
velocity/accel-limited tracking -> controller -> (sim/hardware) ->
/joint_states feedback. Run alongside normal teleop/motion, no need to
inject test commands.

Usage:
    python3 joint_cmd_state_delay.py
    python3 joint_cmd_state_delay.py --joints left_joint_1,right_joint_1
    python3 joint_cmd_state_delay.py --threshold 0.02 --tolerance 0.01 --csv out.csv
"""

import argparse
import csv
import sys
import time
from collections import defaultdict, deque

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class JointCmdStateDelay(Node):

    def __init__(self, cmd_topic, state_topic, joints, threshold,
                 tolerance, timeout, report_interval, history, csv_path):
        super().__init__("joint_cmd_state_delay")

        self.joints = set(joints) if joints else None
        self.threshold = threshold
        self.tolerance = tolerance
        self.timeout = timeout
        self.report_interval = report_interval

        self.last_cmd = {}       # name -> last commanded position
        self.pending = {}        # name -> {"target": float, "t0": float}
        self.latencies = defaultdict(lambda: deque(maxlen=history))
        self.misses = defaultdict(int)

        self.csv_writer = None
        self.csv_file = None
        if csv_path:
            self.csv_file = open(csv_path, "w", newline="")
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(["joint", "t0_recv", "latency_ms"])

        self.create_subscription(JointState, cmd_topic, self.cmd_callback, 10)
        self.create_subscription(JointState, state_topic, self.state_callback, 10)

        self.create_timer(self.report_interval, self.report)

        self.get_logger().info(
            f"Watching {cmd_topic} -> {state_topic} "
            f"(threshold={threshold} rad, tolerance={tolerance} rad, "
            f"timeout={timeout}s)"
        )

    def _wanted(self, name):
        return self.joints is None or name in self.joints

    def cmd_callback(self, msg):
        now = time.monotonic()

        for name, val in zip(msg.name, msg.position):
            if not self._wanted(name):
                continue

            prev = self.last_cmd.get(name)
            self.last_cmd[name] = val

            if prev is None:
                continue

            p = self.pending.get(name)
            if p is None:
                if abs(val - prev) > self.threshold:
                    self.pending[name] = {"target": val, "t0": now}
            else:
                p["target"] = val

    def state_callback(self, msg):
        now = time.monotonic()
        actual = dict(zip(msg.name, msg.position))

        stale = []
        for name, p in self.pending.items():
            if now - p["t0"] > self.timeout:
                stale.append(name)
                self.misses[name] += 1
                continue

            if name not in actual:
                continue

            if abs(actual[name] - p["target"]) <= self.tolerance:
                latency_s = now - p["t0"]
                self.latencies[name].append(latency_s)
                self.get_logger().info(
                    f"{name}: reacted in {latency_s * 1000:.1f} ms "
                    f"(target={p['target']:.4f})"
                )
                if self.csv_writer:
                    self.csv_writer.writerow(
                        [name, f"{p['t0']:.6f}", f"{latency_s * 1000:.3f}"]
                    )
                stale.append(name)

        for name in stale:
            self.pending.pop(name, None)

    def report(self):
        if not self.latencies:
            return

        print("\n" + "=" * 70)
        print("Reaction time (joint_cmd -> joint_states), rolling stats")
        print("=" * 70)

        all_vals = []
        for name in sorted(self.latencies):
            vals = list(self.latencies[name])
            if not vals:
                continue
            all_vals.extend(vals)
            mean_ms = sum(vals) / len(vals) * 1000
            min_ms = min(vals) * 1000
            max_ms = max(vals) * 1000
            miss = self.misses.get(name, 0)
            print(
                f"  {name:28s} n={len(vals):4d}  "
                f"mean={mean_ms:7.1f}ms  min={min_ms:7.1f}ms  "
                f"max={max_ms:7.1f}ms  timeouts={miss}"
            )

        if all_vals:
            mean_ms = sum(all_vals) / len(all_vals) * 1000
            print("-" * 70)
            print(f"  {'OVERALL':28s} n={len(all_vals):4d}  mean={mean_ms:7.1f}ms")
        print("=" * 70)

    def destroy_node(self):
        if self.csv_file:
            self.csv_file.close()
        super().destroy_node()


def main():
    parser = argparse.ArgumentParser(
        description="Measure reaction time between /joint_cmd and /joint_states"
    )
    parser.add_argument("--cmd-topic", default="/joint_cmd")
    parser.add_argument("--state-topic", default="/joint_states")
    parser.add_argument(
        "--joints", type=str, default=None,
        help="Comma-separated joint names to track (default: all joints seen)"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.01,
        help="Min commanded-position jump (rad) that starts a measurement (default: 0.01)"
    )
    parser.add_argument(
        "--tolerance", type=float, default=0.01,
        help="Max |actual - target| (rad) to count as 'reacted' (default: 0.01)"
    )
    parser.add_argument(
        "--timeout", type=float, default=2.0,
        help="Drop a pending measurement if unresolved after this many seconds (default: 2.0)"
    )
    parser.add_argument(
        "--report-interval", type=float, default=5.0,
        help="Seconds between printed summary reports (default: 5.0)"
    )
    parser.add_argument(
        "--history", type=int, default=200,
        help="Rolling window size (samples) kept per joint for stats (default: 200)"
    )
    parser.add_argument(
        "--csv", type=str, default=None,
        help="Optional path to log every measured latency as CSV"
    )

    args, _unknown = parser.parse_known_args()

    joints = None
    if args.joints:
        joints = [j.strip() for j in args.joints.split(",") if j.strip()]

    rclpy.init(args=sys.argv)

    node = JointCmdStateDelay(
        cmd_topic=args.cmd_topic,
        state_topic=args.state_topic,
        joints=joints,
        threshold=args.threshold,
        tolerance=args.tolerance,
        timeout=args.timeout,
        report_interval=args.report_interval,
        history=args.history,
        csv_path=args.csv,
    )

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.report()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
