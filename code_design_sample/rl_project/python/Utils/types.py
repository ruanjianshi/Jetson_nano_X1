# -*- coding: utf-8 -*-
"""
@file types.py
@brief 网格世界环境类型定义
@note 位于 rl_project/python/Utils/ 目录下

本模块定义了强化学习网格世界环境的所有核心类型和常量:

## 通道设计 (Channel Design)
- Channel 0 (K_AGENT_CHANNEL): 智能体位置, 用1.0标记
- Channel 1 (K_GOAL_CHANNEL): 食物/目标位置, 用1.0标记
- Channel 2-5: 障碍物通道, 分别表示从N/E/S/W四个方向移动的障碍物

## 奖励机制 (Reward System)
- 吃食物: +1
- 撞障碍物: -1
- 出界: -2
- 默认: 0

## 状态表示 (State Representation)
智能体观测到的状态是一个33x33大小的窗口, 以智能体为中心.
状态使用6通道的浮点tensor表示, 每个通道33x33=1089个像素, 总计6534维.
"""

from typing import Tuple

# =============================================================================
# 常量定义 - Constants Definition
# =============================================================================

# 通道索引 (Channel Index)
K_AGENT_CHANNEL: int = 0          # 智能体通道 - Agent位置标记为1.0
K_GOAL_CHANNEL: int = 1           # 目标通道 - 食物位置标记为1.0
K_OBSTACLE_N_CHANNEL: int = 2     # 北向障碍物通道 - 从北向南移动
K_OBSTACLE_E_CHANNEL: int = 3     # 东向障碍物通道 - 从东向西移动
K_OBSTACLE_S_CHANNEL: int = 4     # 南向障碍物通道 - 从南向北移动
K_OBSTACLE_W_CHANNEL: int = 5     # 西向障碍物通道 - 从西向东移动
K_CHANNEL_COUNT: int = 6           # 总通道数

# 动作定义 - Action Definition
K_ACTION_COUNT: int = 9            # 动作数量: 8方向 + 原地不动

# 奖励常量 - Reward Constants
K_REWARD_FOOD: int = 1             # 吃到食物的奖励
K_REWARD_OBSTACLE: int = -1        # 撞到障碍物的惩罚
K_REWARD_OUT_OF_BOUNDS: int = -2   # 出界的惩罚
K_REWARD_DEFAULT: int = 0          # 默认奖励

# 状态窗口尺寸 - State Window Size
K_WINDOW_SIZE: int = 33           # 状态窗口边长 (33x33)
K_HALF_SIZE: int = 16             # 半窗大小, 用于计算padding

# 方向向量 - Direction Vectors
# 对应动作: 上, 右上, 右, 右下, 下, 左下, 左, 左上, 原地
K_DIRECTION_ROW: Tuple[int, ...] = (-1, -1, 0, 1, 1, 1, 0, -1, 0)
K_DIRECTION_COL: Tuple[int, ...] = (0, 1, 1, 1, 0, -1, -1, -1, 0)
K_ACTION_CHARS: str = "↑↗→↘↓↙←↖□"  # 动作对应的Unicode字符


# =============================================================================
# 数据结构 - Data Structures
# =============================================================================
#轻量级、不可变的二维坐标数据类
class Position:
    """
    @brief 位置结构体 - 表示网格中的二维坐标
    
    用于表示智能体、食物、障碍物在网格中的位置。
    使用__slots__优化内存占用。
    
    @note row_v: 行坐标 (0-based, 从上往下递增)
    @note col_v: 列坐标 (0-based, 从左往右递增)
    """
    __slots__ = ('row_v', 'col_v')

    def __init__(self, row: int = 0, col: int = 0):
        self.row_v: int = row  # 行坐标
        self.col_v: int = col  # 列坐标

    def __eq__(self, other: 'Position') -> bool:
        """判断两个位置是否相等"""
        return self.row_v == other.row_v and self.col_v == other.col_v

    def __add__(self, other: 'Position') -> 'Position':
        """位置加法, 用于计算新位置 (如: 当前位置 + 方向 = 新位置)"""
        return Position(self.row_v + other.row_v, self.col_v + other.col_v)

    def __repr__(self) -> str:
        """调试友好的字符串表示"""
        return f"Position({self.row_v}, {self.col_v})"


class TransitionResult:
    """
    @brief 转换结果结构体 - 存储step返回的详细信息
    
    @note next_pos_v: 智能体下一步位置
    @note reward_v: 当前步骤获得的奖励
    @note terminal_v: 是否终止 (撞障碍物/出界)
    @note ate_food_v: 是否吃到食物
    @note hit_obstacle_v: 是否撞到障碍物
    """
    __slots__ = ('next_pos_v', 'reward_v', 'terminal_v', 'ate_food_v', 'hit_obstacle_v')

    def __init__(self):
        self.next_pos_v: Position = Position()
        self.reward_v: int = 0
        self.terminal_v: bool = False
        self.ate_food_v: bool = False
        self.hit_obstacle_v: bool = False


class EnvConfig:
    """
    @brief 环境配置结构体 - 定义网格世界环境的参数
    
    @note height_v/width_v: 网格尺寸 (默认64x64)
    @note obstacle_prob_v: 边界生成障碍物的概率
    @note obstacle_freq_v: 障碍物生成频率 (每N步生成一次)
    @note food_count_v: 食物数量
    """
    __slots__ = ('height_v', 'width_v', 'obstacle_prob_v', 'obstacle_freq_v', 'food_count_v')

    def __init__(self,
                 height: int = 64,
                 width: int = 64,
                 obstacle_prob: float = 0.05,
                 obstacle_freq: int = 20,
                 food_count: int = 20):
        self.height_v: int = height                    # 网格高度
        self.width_v: int = width                      # 网格宽度
        self.obstacle_prob_v: float = obstacle_prob    # 障碍物生成概率
        self.obstacle_freq_v: int = obstacle_freq      # 障碍物生成频率
        self.food_count_v: int = food_count            # 食物数量


class StepResult:
    """
    @brief Step结果结构体 - 强化学习环境的step()返回值
    
    @note state_v: 新状态 (展平的tensor列表)
    @note reward_v: 获得的奖励
    @note terminal_v: 是否终止
    """
    __slots__ = ('state_v', 'reward_v', 'terminal_v')

    def __init__(self):
        self.state_v: list = []
        self.reward_v: float = 0.0
        self.terminal_v: bool = False


class Transition:
    """
    @brief 转换元组 - 存储(s, a, r, s', terminal)经验
    
    用于DQN的experience replay机制。
    
    @note state_v: 当前状态
    @note action_v: 采取的动作 (0-8)
    @note reward_v: 获得的奖励
    @note next_state_v: 下一个状态
    @note terminal_v: 是否终止
    """
    __slots__ = ('state_v', 'action_v', 'reward_v', 'next_state_v', 'terminal_v')

    def __init__(self):
        self.state_v: list = []
        self.action_v: int = 0
        self.reward_v: float = 0.0
        self.next_state_v: list = []
        self.terminal_v: bool = False


class DQNConfig:
    """
    @brief DQN智能体配置结构体
    
    @note state_dim_v: 状态维度 (默认6*33*33=6534)
    @note action_dim_v: 动作维度 (默认9)
    @note learning_rate_v: 学习率
    @note gamma_v: 折扣因子
    @note epsilon_*: 探索率相关参数
    @note batch_size_v: 批大小
    @note memory_capacity_v: 经验回放缓冲区容量
    """
    __slots__ = ('state_dim_v', 'action_dim_v', 'learning_rate_v', 'gamma_v',
                 'epsilon_start_v', 'epsilon_end_v', 'epsilon_decay_steps_v',
                 'batch_size_v', 'memory_capacity_v', 'target_update_freq_v')

    def __init__(self):
        self.state_dim_v: int = K_CHANNEL_COUNT * K_WINDOW_SIZE * K_WINDOW_SIZE  # 6534
        self.action_dim_v: int = K_ACTION_COUNT  # 9
        self.learning_rate_v: float = 0.001      # 学习率
        self.gamma_v: float = 0.99               # 折扣因子
        self.epsilon_start_v: float = 1.0        # 初始探索率
        self.epsilon_end_v: float = 0.01         # 最终探索率
        self.epsilon_decay_steps_v: int = 10000   # 探索率衰减步数
        self.batch_size_v: int = 32              # 批大小
        self.memory_capacity_v: int = 10000      # 经验池容量
        self.target_update_freq_v: int = 100     # 目标网络更新频率