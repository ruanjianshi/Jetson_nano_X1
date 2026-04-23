# Motor Command Message - Zhiyuan PowerFlow R Series Protocol
# 电机控制指令消息

# 控制命令
uint8 CMD_ENABLE = 1      # 使能电机
uint8 CMD_DISABLE = 2     # 禁能电机
uint8 CMD_SET_MODE = 3    # 设置控制模式
uint8 CMD_MIT = 4         # MIT模式控制 (位置+速度+力矩+刚度+阻尼)

# 控制模式 (用于 CMD_SET_MODE)
uint8 MODE_CURRENT = 0         # 电流环模式
uint8 MODE_CURRENT_RAMP = 1     # 电流环梯形加减速
uint8 MODE_VELOCITY = 2         # 速度环模式
uint8 MODE_VELOCITY_RAMP = 3    # 速度环梯形加减速
uint8 MODE_POSITION = 4         # 位置环模式
uint8 MODE_POSITION_RAMP = 5    # 位置环梯形加减速
uint8 MODE_MIT = 6             # MIT混合控制模式 (默认)

# CAN通道
uint8 CHANNEL_CTRL1 = 1        # CTRL1通道 (连接R86-2)
uint8 CHANNEL_CTRL2 = 2       # CTRL2通道 (连接R52)
uint8 CHANNEL_CTRL3 = 3       # CTRL3通道

# 电机型号
string TYPE_R86 = "POWER_FLOW_R86"   # R86-2大功率电机
string TYPE_R52 = "POWER_FLOW_R52"   # R52小功率电机
string TYPE_R28 = "POWER_FLOW_R28"   # R28微型电机

uint8 cmd              # 命令: 1=使能, 2=禁能, 3=设置模式, 4=MIT控制
uint8 motor_id         # 电机 CAN ID (1-8)
uint8 channel         # CAN通道: 1=CTRL1, 2=CTRL2, 3=CTRL3 (默认1)
string motor_type      # 电机型号: POWER_FLOW_R86/R52/R28 (用于校验)
uint8 mode             # 控制模式 (仅CMD_SET_MODE时使用)
float32 q              # 目标位置 (rad)
float32 dq             # 目标速度 (rad/s)
float32 tau            # 目标力矩 (Nm), CMD_MIT时必填
float32 kp             # 刚度 (0-500), CMD_MIT时必填
float32 kd             # 阻尼 (0-8), CMD_MIT时必填
