import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import PoseStamped
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class QuestTFBroadcasterMirrored(Node):
    def __init__(self):
        super().__init__('quest_tf_broadcaster_mirrored')
        self.br = TransformBroadcaster(self)
        self.create_subscription(PoseStamped, '/quest/head', lambda msg: self.broadcast(msg, 'quest_head', False), 10)
        self.create_subscription(PoseStamped, '/quest/left/pose', lambda msg: self.broadcast(msg, 'quest_right', True), 10)
        self.create_subscription(PoseStamped, '/quest/right/pose', lambda msg: self.broadcast(msg, 'quest_left', True), 10)

    def broadcast(self, msg, frame_id, swap_yaw):
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'world'
        t.child_frame_id = frame_id
        t.transform.translation.x =  msg.pose.position.z
        t.transform.translation.y =  msg.pose.position.x
        t.transform.translation.z =  msg.pose.position.y
        t.transform.rotation.x =  msg.pose.orientation.z
        t.transform.rotation.y =  msg.pose.orientation.x
        t.transform.rotation.z =  msg.pose.orientation.y if swap_yaw else -msg.pose.orientation.y
        t.transform.rotation.w =  msg.pose.orientation.w
        self.br.sendTransform(t)

def main():
    rclpy.init()
    node = QuestTFBroadcasterMirrored()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
