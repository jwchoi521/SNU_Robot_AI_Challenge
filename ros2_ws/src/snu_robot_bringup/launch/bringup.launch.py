from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _package_file(*parts: str) -> PathJoinSubstitution:
    return PathJoinSubstitution([FindPackageShare("snu_robot_bringup"), *parts])


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time")
    enable_sensor_tf = LaunchConfiguration("enable_sensor_tf")
    enable_ekf = LaunchConfiguration("enable_ekf")
    enable_slam = LaunchConfiguration("enable_slam")
    enable_nav2 = LaunchConfiguration("enable_nav2")
    enable_rviz = LaunchConfiguration("enable_rviz")
    scan_topic = LaunchConfiguration("scan_topic")

    sensor_tf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_package_file("launch", "sensor_tf.launch.py")),
        condition=IfCondition(enable_sensor_tf),
    )

    ekf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_package_file("launch", "ekf.launch.py")),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
        condition=IfCondition(enable_ekf),
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_package_file("launch", "slam.launch.py")),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "scan_topic": scan_topic,
        }.items(),
        condition=IfCondition(enable_slam),
    )

    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_package_file("launch", "navigation.launch.py")),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
        condition=IfCondition(enable_nav2),
    )

    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(_package_file("launch", "rviz.launch.py")),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
        condition=IfCondition(enable_rviz),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("scan_topic", default_value="/scan"),
            DeclareLaunchArgument("enable_sensor_tf", default_value="true"),
            DeclareLaunchArgument("enable_ekf", default_value="true"),
            DeclareLaunchArgument("enable_slam", default_value="true"),
            DeclareLaunchArgument("enable_nav2", default_value="true"),
            DeclareLaunchArgument("enable_rviz", default_value="false"),
            sensor_tf_launch,
            ekf_launch,
            slam_launch,
            nav_launch,
            rviz_launch,
        ]
    )
