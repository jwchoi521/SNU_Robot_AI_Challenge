# 빌드 및 테스트 메모

이 프로젝트는 ROS 2 Jazzy 기준으로 검증합니다. Windows의 한글 사용자 경로 아래에서 WSL `/mnt/c/...`
경로를 그대로 사용하면 `rosidl` 메시지 생성 과정에서 경로 인코딩 문제가 발생할 수 있습니다.

따라서 Windows에서 작업하더라도 실제 `colcon build` 검증은 WSL 내부의 ASCII 경로에서 수행하는 것을
권장합니다.

## 권장 검증 절차

```bash
rm -rf /root/snu_robot_ai_challenge_verify
mkdir -p /root/snu_robot_ai_challenge_verify/ros2_ws
cp -a /mnt/c/Users/<사용자명>/path/to/SNU_Robot_AI_Challenge/ros2_ws/src \
  /root/snu_robot_ai_challenge_verify/ros2_ws/

cd /root/snu_robot_ai_challenge_verify/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

## 현재 확인된 결과

- WSL `Ubuntu-24.04` + ROS 2 Jazzy 환경에서 `colcon build --symlink-install` 통과
- `snu_base_control`, `snu_target_navigation`, `snu_mission_manager`에 최소 import 테스트 추가
- 위 ASCII 경로 검증 방식에서 `colcon test` 통과

## 주의

원래 저장소 경로가 한글 Windows 사용자 폴더에 있을 경우, 코드가 맞더라도 ROS 2 메시지 생성기가
중간 산출물 경로를 잘못 해석할 수 있습니다. Jetson이나 Ubuntu 로컬 디스크처럼 UTF-8/ASCII 경로가
안정적인 환경에서는 해당 문제가 재현되지 않을 가능성이 큽니다.
