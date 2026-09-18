from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessStart
from pathlib import Path
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    use_cpp_vcan_bridge_arg = DeclareLaunchArgument(
        "use_cpp_vcan_bridge",
        default_value="true",
        description="Use the C++ vcan_bridge_node (hw_interface) instead of the "
                     "Python vcan_bridge node (gen2). Only one may run at a time: "
                     "both bind the same CANalyst-II USB device and vcan0/vcan1.",
    )
    use_cpp_vcan_bridge = LaunchConfiguration("use_cpp_vcan_bridge")

    vcan_bridge_node_cpp = Node(
        package="hw_interface",
        executable="vcan_bridge_node",
        output="screen",
        condition=IfCondition(use_cpp_vcan_bridge),
    )

    vcan_bridge_node_py = Node(
        package="gen2",
        executable="vcan_bridge",
        output="screen",
        condition=UnlessCondition(use_cpp_vcan_bridge),
    )

    gravity_torque_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("dynamics"),
                "launch",
                "gravity_torque.launch.py",
            )
        )
    )
    gesture_management_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gesture_management"),
                "launch",
                "gesture_management.launch.py",
            )
        )
    )
    joint_analyzer_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("joint_analyzer"),
                "launch",
                "joint_analyzer.launch.py",
            )
        )
    )
    joint_cmd_logger_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("joint_cmd_logger"),
                "launch",
                "joint_cmd_logger.launch.py",
            )
        )
    )
    client_ui_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("daksha_ui"),
                "launch",
                "client_ui.launch.py",
            )
        )
    )
    vajara_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("vajara"),
                "launch",
                "vajara.launch.py",
            )
        )
    )

    urdf = Path(
        os.path.join(
            get_package_share_directory("daksha_description_full_body"),
            "urdf",
            "robot.urdf",
        )
    ).read_text()

    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            os.path.join(
                get_package_share_directory("gen2"), "config", "controllers.yaml"
            ),
            {"robot_description": urdf},
        ],
        output="screen",
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": urdf}],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )
    left_arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["left_arm_mit_controller"],
        output="screen",
    )

    right_arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["right_arm_mit_controller"],
        output="screen",
    )

    left_gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["left_gripper_mit_controller"],
        output="screen",
    )

    right_gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["right_gripper_mit_controller"],
        output="screen",
    )



    joint_command_node = Node(
        package="gen2",
        executable="joint_cmd",
        output="screen",
        parameters=[{"enforce_joint_limits": False}],
    )
    GravityToJointCmd_node = Node(
        package="gen2",
        executable="GravityToJointCmd",
        output="screen",
    )
    joint_cmd_publisher_from_joint_sates_node = Node(
        package="gen2",
        executable="joint_cmd_publisher_from_joint_sates",
        output="screen",
        parameters=[{"publish_joint_cmd": False}],
    )
    teach_mode_node = Node(
        package="gen2",
        executable="teach_mode_node",
        output="screen",
        parameters=[{"teach_mode": True}],
    )
    gravity_scale_setter_node = Node(
        package="gen2",
        executable="gravity_scale_setter",
        output="screen",
    )
    mode_toggler_node = Node(
        package="gen2",
        executable="mode_toggler",
        output="screen",
        parameters=[{"mode": "teach"}],
    )
    vr_management_ui_node = Node(
        package="vr_teleop",
        executable="vr_management_ui",
        output="screen",
        parameters=[{"enabled": False}],
    )
    vr_pose_relay_node = Node(
        package="vr_teleop",
        executable="vr_pose_relay",
        output="screen",
    )
    ik_node = Node(
        package="kinematics",
        executable="ik_node",
        output="screen",
    )
    # vr_gripper_ctrl_node = Node(
    #     package="vr_teleop",
    #     executable="vr_gripper_ctrl",
    #     output="screen",
    # )
    battery_info_node = Node(
        package="gen2",
        executable="battery_info",
        output="screen",
    )
    home_move_service_node = Node(
        package="gen2",
        executable="HomeMoveService",
        output="screen",
    )

    leader_controller_ui_node = Node(
        package="gen2",
        executable="leader_controller_ui",
        output="screen",
    )

    arm_recovery_watchdog_node = Node(
        package="gen2",
        executable="arm_recovery_watchdog",
        output="screen",
    )

    return LaunchDescription([
        use_cpp_vcan_bridge_arg,
        vcan_bridge_node_cpp,
        vcan_bridge_node_py,
        TimerAction(
            period=5.0,
            actions=[
                gravity_torque_launch,
                gesture_management_launch,
                # joint_analyzer_launch,
                # client_ui_launch,
                # vajara_launch,
                controller_manager,
                robot_state_publisher,
                RegisterEventHandler(
                    OnProcessStart(
                        target_action=controller_manager,
                        on_start=[
                            joint_state_broadcaster,
                            left_arm_controller,
                            right_arm_controller,
                            left_gripper_controller,
                            right_gripper_controller,
                            joint_command_node,
                            GravityToJointCmd_node,
                            joint_cmd_publisher_from_joint_sates_node,
                            gravity_scale_setter_node,
                            teach_mode_node,
                            mode_toggler_node,
                            # vr_management_ui_node,
                            # vr_pose_relay_node,
                            ik_node,
                            # vr_gripper_ctrl_node,
                            # battery_info_node,
                            home_move_service_node,
                            leader_controller_ui_node,
                            # arm_recovery_watchdog_node,
                        ],
                    )
                ),
            ],
        ),
    ])