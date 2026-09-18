import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import TransformStamped
from std_msgs.msg import Bool
from std_srvs.srv import SetBool
from tf2_ros import TransformBroadcaster


class QuestTFSwitch(Node):
    """Broadcasts Quest poses as TF, switching between normal and mirrored at runtime.

    Service ~/set_mirror (std_srvs/SetBool): data=True -> mirrored, data=False -> normal.
    Topic   ~/mirror_state (std_msgs/Bool, latched): the mode currently in effect.
    """

    def __init__(self):
        super().__init__('quest_tf_switch')

        self.declare_parameter('mirror', False)
        # The original quest_tf_mirror node left the head's yaw un-mirrored so the
        # operator's gaze direction stays intuitive. Default preserves that.
        self.declare_parameter('mirror_head_yaw', False)

        self.mirror = self.get_parameter('mirror').value
        self.mirror_head_yaw = self.get_parameter('mirror_head_yaw').value

        self.br = TransformBroadcaster(self)

        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.state_pub = self.create_publisher(Bool, '~/mirror_state', latched)

        self.create_subscription(PoseStamped, '/quest/head', lambda msg: self.broadcast(msg, 'head'), 10)
        self.create_subscription(PoseStamped, '/quest/left/pose', lambda msg: self.broadcast(msg, 'left'), 10)
        self.create_subscription(PoseStamped, '/quest/right/pose', lambda msg: self.broadcast(msg, 'right'), 10)

        self.create_service(SetBool, '~/set_mirror', self.set_mirror)

        self.publish_state()
        self.get_logger().info('quest_tf_switch started in %s mode' % self.mode_name())

    def mode_name(self):
        return 'MIRRORED' if self.mirror else 'NORMAL'

    def publish_state(self):
        self.state_pub.publish(Bool(data=self.mirror))

    def set_mirror(self, request, response):
        changed = request.data != self.mirror
        self.mirror = request.data
        if changed:
            self.publish_state()
            self.get_logger().info('switched to %s mode' % self.mode_name())
        response.success = True
        response.message = self.mode_name()
        return response

    def resolve_frame(self, source):
        """Map the source topic onto a TF frame; mirroring swaps the two hands."""
        if source == 'head':
            return 'quest_head'
        if self.mirror:
            return 'quest_right' if source == 'left' else 'quest_left'
        return 'quest_left' if source == 'left' else 'quest_right'

    def broadcast(self, msg, source):
        p = msg.pose.position
        q = msg.pose.orientation

        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'world'
        t.child_frame_id = self.resolve_frame(source)

        if self.mirror:
            # Unity (LH, X right / Y up / Z fwd) -> ROS FLU, then mirrored across the XZ plane.
            # Reflecting a rotation through the plane normal to Y negates its X and Z axis
            # components, which reduces to dropping every sign flip of the normal mapping.
            t.transform.translation.x = p.z
            t.transform.translation.y = p.x
            t.transform.translation.z = p.y
            t.transform.rotation.x = q.z
            t.transform.rotation.y = q.x
            t.transform.rotation.z = q.y if (source != 'head' or self.mirror_head_yaw) else -q.y
            t.transform.rotation.w = q.w
        else:
            # Standard Unity -> ROS FLU conversion. The negated w reverses the rotation
            # direction, which the left- to right-handed relabelling requires.
            t.transform.translation.x = p.z
            t.transform.translation.y = -p.x
            t.transform.translation.z = p.y
            t.transform.rotation.x = q.z
            t.transform.rotation.y = -q.x
            t.transform.rotation.z = q.y
            t.transform.rotation.w = -q.w

        self.br.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = QuestTFSwitch()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
