from roomba_python import discover_robots, get_robot_public_info

robots = discover_robots(timeout=2.0)
print(f"discovered {len(robots)} robot(s)")

for robot in robots:
    print(robot.model_dump())

if robots:
    details = get_robot_public_info(robots[0].ip, timeout=2.0)
    print("details for first robot:")
    print(details.model_dump())
