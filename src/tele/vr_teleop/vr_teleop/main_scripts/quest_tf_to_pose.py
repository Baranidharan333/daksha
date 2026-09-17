"""Bridges quest_tf_switch's TF frames back to the PoseStamped topics ik_node expects.

kinematics/ik_node.py subscribes to /left/pose and /right/pose (geometry_msgs/PoseStamped)
per arm. quest_tf_switch broadcasts the same controller poses as TF instead
(world -> quest_left / quest_right), already Unity->ROS FLU converted and with
mirroring applied if enabled. This node looks those transforms up on a timer
and republishes them as the PoseStamped topics, so ik_node needs no changes.
"""

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from geometry_msgs.msg import PoseStamped
from tf2_ros import Buffer, TransformException, TransformListener

# arm name -> (TF child frame from quest_tf_switch, output topic ik_node subscribes to)
ARMS = {
    "left": ("quest_left", "/left/pose"),
    "right": ("quest_right", "/right/pose"),
}


class QuestTFToPose(Node):

    def __init__(self):
        super().__init__("quest_tf_to_pose")

        self.declare_parameter("world_frame", "world")
        self.world_frame = self.get_parameter("world_frame").get_parameter_value().string_value

        self.declare_parameter("lookup_rate", 100.0)
        lookup_rate = self.get_parameter("lookup_rate").get_parameter_value().double_value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.pubs = {
            arm: self.create_publisher(PoseStamped, topic, 10)
            for arm, (_frame, topic) in ARMS.items()
        }

        # No Quest client is connected yet at launch, so "world" hasn't been
        # broadcast and every lookup would just fail. Wait for the first raw
        # pose from the client (proof it's actually connected and sending)
        # before starting the lookup timer, instead of polling/warning from
        # startup.
        self.client_connected = False
        self._connect_subs = [
            self.create_subscription(
                PoseStamped, f"/quest/{arm}/pose",
                self._on_client_connected, 10,
            )
            for arm in ARMS
        ]

        self.create_timer(1.0 / lookup_rate, self.lookup_cb)

        self.get_logger().info(
            f"quest_tf_to_pose started: waiting for a Quest client to connect "
            f"before looking up {self.world_frame} -> "
            f"{', '.join(frame for frame, _ in ARMS.values())}"
        )

    def _on_client_connected(self, _msg):
        if self.client_connected:
            return

        self.client_connected = True

        for sub in self._connect_subs:
            self.destroy_subscription(sub)
        self._connect_subs = []

        self.get_logger().info("Quest client connected, starting TF lookups")

    def lookup_cb(self):
        if not self.client_connected:
            return

        for arm, (frame, _topic) in ARMS.items():
            try:
                tf = self.tf_buffer.lookup_transform(self.world_frame, frame, Time())
            except TransformException as exc:
                self.get_logger().warn(
                    f"{self.world_frame} -> {frame} unavailable: {exc}",
                    throttle_duration_sec=2.0,
                )
                continue

            msg = PoseStamped()
            msg.header.stamp = tf.header.stamp
            msg.header.frame_id = self.world_frame

            msg.pose.position.x = tf.transform.translation.x
            msg.pose.position.y = tf.transform.translation.y
            msg.pose.position.z = tf.transform.translation.z

            msg.pose.orientation.x = tf.transform.rotation.x
            msg.pose.orientation.y = tf.transform.rotation.y
            msg.pose.orientation.z = tf.transform.rotation.z
            msg.pose.orientation.w = tf.transform.rotation.w

            self.pubs[arm].publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = QuestTFToPose()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
