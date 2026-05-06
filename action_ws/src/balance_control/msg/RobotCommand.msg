# Robot Command Message
# 用于描述机器人的高层运动命令

uint8 CMD_STOP = 0           # 停止
uint8 CMD_FORWARD = 1        # 前进
uint8 CMD_BACKWARD = 2        # 后退
uint8 CMD_TURN_LEFT = 3      # 左转
uint8 CMD_TURN_RIGHT = 4     # 右转
uint8 CMD_STRAFE_LEFT = 5     # 左侧向移动
uint8 CMD_STRAFE_RIGHT = 6    # 右侧向移动
uint8 CMD_JUMP = 7           # 跳跃
uint8 CMD_BALANCE = 8        # 进入平衡模式

uint8 command                # 命令类型
float64 speed                # 速度 m/s (0.0 ~ 2.0)
float64 yaw_rate            # 偏航角速度 rad/s (0.0 ~ 3.14)
float64 jump_height          # 跳跃高度 m (0.0 ~ 0.5)
float64 duration             # 命令持续时间 s (0.0 = 持续)