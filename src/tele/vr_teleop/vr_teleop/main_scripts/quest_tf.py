import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import PoseStamped
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class QuestTFBroadcaster(Node):
    def __init__(self):
        super().__init__('quest_tf_broadcaster')
        self.br = TransformBroadcaster(self)
        self.create_subscription(PoseStamped, '/quest/head', lambda msg: self.broadcast(msg, 'quest_head'), 10)
        self.create_subscription(PoseStamped, '/quest/left/pose', lambda msg: self.broadcast(msg, 'quest_left'), 10)
        self.create_subscription(PoseStamped, '/quest/right/pose', lambda msg: self.broadcast(msg, 'quest_right'), 10)

    def broadcast(self, msg, frame_id):
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'world'
        t.child_frame_id = frame_id
        t.transform.translation.x =  msg.pose.position.z
        t.transform.translation.y = -msg.pose.position.x
        t.transform.translation.z =  msg.pose.position.y
        t.transform.rotation.x =  msg.pose.orientation.z
        t.transform.rotation.y = -msg.pose.orientation.x
        t.transform.rotation.z =  msg.pose.orientation.y
        t.transform.rotation.w = -msg.pose.orientation.w
        self.br.sendTransform(t)

def main():
    rclpy.init()
    node = QuestTFBroadcaster()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        # launch sends SIGINT on teardown and rclpy's own handler has already
        # shut the context down by the time we get here; calling shutdown again
        # raises RCLError and turns a clean stop into a spurious exit code 1.
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
