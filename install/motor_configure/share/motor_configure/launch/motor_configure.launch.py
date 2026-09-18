from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # Default matches vcan_bridge's output (vcan0/vcan1, bridged from its
    # physical CAN0/CAN1), since that node is what runs alongside this one
    # by default (see run_vcan_bridge below). There is no "can0" SocketCAN
    # device on machines that only have the physical adapter vcan_bridge
    # talks to directly -- pass channel:=can0 explicitly if this ever runs
    # on a machine with a real can0 interface instead.
    channel_arg = DeclareLaunchArgument(
        "channel",
        default_value="vcan0",
        description="SocketCAN interface name to open on startup (e.g. vcan0, can0)",
    )
    host_arg = DeclareLaunchArgument(
        "host",
        default_value="0.0.0.0",
        description="Bind address for the web server",
    )
    port_arg = DeclareLaunchArgument(
        "port",
        default_value="8000",
        description="Bind port for the web server",
    )
    run_vcan_bridge_arg = DeclareLaunchArgument(
        "run_vcan_bridge",
        default_value="true",
        description=(
            "Also launch gen2's vcan_bridge node (bridges a physical "
            "canalystii CAN adapter to vcan0/vcan1). Requires that hardware "
            "and VCAN_SUDO_PASSWORD in the environment; set to false to "
            "skip it, e.g. when pointing --channel at an interface that "
            "already exists."
        ),
    )

    motor_configure_node = Node(
        package="motor_configure",
        executable="motor_configure",
        name="motor_configure",
        output="screen",
        parameters=[{
            "channel": LaunchConfiguration("channel"),
            "host": LaunchConfiguration("host"),
            "port": LaunchConfiguration("port"),
        }],
    )

    vcan_bridge_node = Node(
        package="gen2",
        executable="vcan_bridge",
        name="dual_can_bridge",
        output="screen",
        condition=IfCondition(LaunchConfiguration("run_vcan_bridge")),
    )

    # vcan_bridge creates vcan0/vcan1 via a few sudo calls at startup, which
    # takes a moment -- give it a head start before motor_configure tries to
    # open its channel, or it can race and hit "No such device".
    delayed_motor_configure_node = TimerAction(period=2.0, actions=[motor_configure_node])

    return LaunchDescription([
        channel_arg,
        host_arg,
        port_arg,
        run_vcan_bridge_arg,
        vcan_bridge_node,
        delayed_motor_configure_node,
    ])
