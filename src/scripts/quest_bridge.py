import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped


class QuestBridge(Node):

    def __init__(self):

        super().__init__("quest_bridge")

        # =====================================================
        # SUBSCRIBERS
        # =====================================================

        self.create_subscription(
            PoseStamped,
            "/quest/left/pose",
            self.left_callback,
            10
        )

        self.create_subscription(
            PoseStamped,
            "/quest/right/pose",
            self.right_callback,
            10
        )

        # =====================================================
        # PUBLISHERS
        # =====================================================

        self.left_pub = self.create_publisher(
            PoseStamped,
            "/left_arm_target",
            10
        )

        self.right_pub = self.create_publisher(
            PoseStamped,
            "/right_arm_target",
            10
        )

        print("QUEST BRIDGE STARTED")

    # =========================================================
    # LEFT CALLBACK
    # =========================================================

    def left_callback(self, msg):

        out = PoseStamped()

        out.header = msg.header

        # -----------------------------------------------------
        # POSITION
        # -----------------------------------------------------

        out.pose.position.x = msg.pose.position.x
        out.pose.position.y = msg.pose.position.y
        out.pose.position.z = msg.pose.position.z

        # -----------------------------------------------------
        # ORIENTATION
        # -----------------------------------------------------

        out.pose.orientation.x = msg.pose.orientation.x
        out.pose.orientation.y = msg.pose.orientation.y
        out.pose.orientation.z = msg.pose.orientation.z
        out.pose.orientation.w = msg.pose.orientation.w

        # -----------------------------------------------------
        # PUBLISH
        # -----------------------------------------------------

        self.left_pub.publish(out)

    # =========================================================
    # RIGHT CALLBACK
    # =========================================================

    def right_callback(self, msg):

        out = PoseStamped()

        out.header = msg.header

        # -----------------------------------------------------
        # POSITION
        # -----------------------------------------------------

        out.pose.position.x = msg.pose.position.x
        out.pose.position.y = msg.pose.position.y
        out.pose.position.z = msg.pose.position.z

        # -----------------------------------------------------
        # ORIENTATION
        # -----------------------------------------------------

        out.pose.orientation.x = msg.pose.orientation.x
        out.pose.orientation.y = msg.pose.orientation.y
        out.pose.orientation.z = msg.pose.orientation.z
        out.pose.orientation.w = msg.pose.orientation.w

        # -----------------------------------------------------
        # PUBLISH
        # -----------------------------------------------------

        self.right_pub.publish(out)


# =============================================================
# MAIN
# =============================================================

def main():

    rclpy.init()

    node = QuestBridge()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":

    main()
