# -*- coding: utf-8 -*-
"""
@file types.py
@brief 网格世界环境类型定义
@note 位于 rl_project/Utils/ 目录下

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
# 每个通道代表一种实体类型, 用不同的bit位表示
K_AGENT_CHANNEL: int = 0          # 智能体通道 - Agent位置标记为1.0
K_GOAL_CHANNEL: int = 1           # 目标通道 - 食物位置标记为1.0
K_OBSTACLE_N_CHANNEL: int = 2     # 北向障碍物通道 - 从北向南移动的障碍物
K_OBSTACLE_E_CHANNEL: int = 3     # 东向障碍物通道 - 从东向西移动的障碍物
K_OBSTACLE_S_CHANNEL: int = 4     # 南向障碍物通道 - 从南向北移动的障碍物
K_OBSTACLE_W_CHANNEL: int = 5     # 西向障碍物通道 - 从西向东移动的障碍物
K_CHANNEL_COUNT: int = 6           # 总通道数 - Agent(0) + Goal(1) + 4个Obstacle(2-5)

# 动作定义 - Action Definition
# 智能体可以执行的动作数量: 8个方向移动 + 1个原地不动 = 9个动作
K_ACTION_COUNT: int = 9

# 奖励常量 - Reward Constants
# 强化学习中奖励值的设计非常重要:
# - 吃食物获得正向奖励, 鼓励智能体寻找食物
# - 撞障碍物/出界获得负向奖励, 惩罚导致死亡的行为
K_REWARD_FOOD: int = 1             # 吃到食物的奖励 - 正向激励
K_REWARD_OBSTACLE: int = -1        # 撞到障碍物的惩罚 - 负向激励
K_REWARD_OUT_OF_BOUNDS: int = -2   # 出界的惩罚 - 比撞障碍物更重,防止越界
K_REWARD_DEFAULT: int = 0           # 默认奖励 - 每一步的基础奖励

# 状态窗口尺寸 - State Window Size
# 智能体只能感知周围33x33的区域, 而不是整个64x64地图
# 这样可以: 1)减少状态空间维度 2)模拟局部视野
K_WINDOW_SIZE: int = 33           # 状态窗口边长 (33x33)
K_HALF_SIZE: int = 16             # 半窗大小, 用于计算以智能体为中心的窗口边界
                                  # 窗口范围: [agent_pos - 16, agent_pos + 16]
                                  # 16 + 1 + 16 = 33, 加1因为Python的range是左闭右开

# 方向向量 - Direction Vectors
# 定义9个动作对应的行/列偏移量
# 索引对应: 0=上, 1=右上, 2=右, 3=右下, 4=下, 5=左下, 6=左, 7=左上, 8=不动
# 例如: 动作0(上)表示行-1(向上移动), 列不变(0)
K_DIRECTION_ROW: Tuple[int, ...] = (-1, -1, 0, 1, 1, 1, 0, -1, 0)
K_DIRECTION_COL: Tuple[int, ...] = (0, 1, 1, 1, 0, -1, -1, -1, 0)
K_ACTION_CHARS: str = "↑↗→↘↓↙←↖□"  # 动作对应的Unicode字符, 用于可视化显示


# =============================================================================
# 数据结构 - Data Structures
# =============================================================================

class Position:
    """
    @brief 位置结构体 - 表示网格中的二维坐标
    
    用于表示智能体、食物、障碍物在网格中的位置。
    使用__slots__优化内存占用, 避免动态字典创建。
    
    @note row_v: 行坐标 (0-based, 从上往下递增, 即Y轴)
    @note col_v: 列坐标 (0-based, 从左往右递增, 即X轴)
    
    @example
        pos = Position(10, 5)  # 创建在第10行第5列的位置
        print(pos.row_v, pos.col_v)  # 输出: 10, 5
    """
    # __slots__ 限制此类只能有row_v和col_v两个属性, 减少内存占用
    __slots__ = ('row_v', 'col_v')

    def __init__(self, row: int = 0, col: int = 0):
        """
        @brief 构造函数
        
        @param row: 行坐标, 默认0
        @param col: 列坐标, 默认0
        """
        self.row_v: int = row  # 行坐标 (Y轴)
        self.col_v: int = col  # 列坐标 (X轴)

    def __eq__(self, other: 'Position') -> bool:
        """
        @brief 判断两个位置是否相等
        
        @param other: 另一个Position对象
        @return True如果位置坐标完全相同
        """
        return self.row_v == other.row_v and self.col_v == other.col_v

    def __add__(self, other: 'Position') -> 'Position':
        """
        @brief 位置加法, 用于计算新位置
        
        将当前位置加上方向向量得到新位置。
        @param other: 另一个Position(通常表示方向偏移)
        @return 新位置
        
        @example
            current = Position(10, 10)
            direction = Position(-1, 0)  # 向上
            new_pos = current + direction  # Position(9, 10)
        """
        return Position(self.row_v + other.row_v, self.col_v + other.col_v)

    def __repr__(self) -> str:
        """
        @brief 调试友好的字符串表示
        
        @return 格式化的位置字符串
        """
        return f"Position({self.row_v}, {self.col_v})"


class TransitionResult:
    """
    @brief 转换结果结构体 - 存储step返回的详细信息
    
    记录智能体执行动作后的完整结果, 包括新位置、奖励、是否终止等。
    
    @note next_pos_v: 智能体执行动作后的新位置
    @note reward_v: 当前步骤获得的奖励值
    @note terminal_v: 是否终止 (True=episode结束)
    @note ate_food_v: 是否吃到食物
    @note hit_obstacle_v: 是否撞到障碍物
    """
    __slots__ = ('next_pos_v', 'reward_v', 'terminal_v', 'ate_food_v', 'hit_obstacle_v')

    def __init__(self):
        """@brief 构造函数, 初始化所有属性为默认值"""
        self.next_pos_v: Position = Position()  # 默认原点
        self.reward_v: int = 0                  # 默认无奖励
        self.terminal_v: bool = False            # 默认不终止
        self.ate_food_v: bool = False            # 默认没吃食物
        self.hit_obstacle_v: bool = False        # 默认没撞障碍物


class EnvConfig:
    """
    @brief 环境配置结构体 - 定义网格世界环境的参数
    
    包含环境的物理参数, 如网格大小、障碍物密度等。
    不同配置会产生不同难度的学习任务。
    
    @note height_v: 网格高度 (行数)
    @note width_v: 网格宽度 (列数)
    @note obstacle_prob_v: 边界生成障碍物的概率 (每格)
    @note obstacle_freq_v: 障碍物重新生成频率 (每N步)
    @note food_count_v: 同时存在的食物数量
    
    @example
        # 创建简单环境
        config = EnvConfig(height=32, width=32, obstacle_prob=0.01)
        
        # 创建困难环境
        config = EnvConfig(height=64, width=64, obstacle_prob=0.1)
    """
    __slots__ = ('height_v', 'width_v', 'obstacle_prob_v', 'obstacle_freq_v', 'food_count_v')

    def __init__(self,
                 height: int = 64,
                 width: int = 64,
                 obstacle_prob: float = 0.05,
                 obstacle_freq: int = 20,
                 food_count: int = 20):
        """
        @brief 构造函数
        
        @param height: 网格高度, 默认64
        @param width: 网格宽度, 默认64
        @param obstacle_prob: 边缘障碍物生成概率, 默认0.05 (5%)
        @param obstacle_freq: 障碍物刷新频率, 默认20步刷新一次
        @param food_count: 食物数量, 默认20个
        
        @note obstacle_prob=0.05 意味着64列的边缘约有0.05*64=3.2个障碍物
        """
        self.height_v: int = height                    # 网格高度 (行数)
        self.width_v: int = width                      # 网格宽度 (列数)
        self.obstacle_prob_v: float = obstacle_prob    # 每格生成障碍物的概率
        self.obstacle_freq_v: int = obstacle_freq      # 每隔多少步刷新障碍物
        self.food_count_v: int = food_count            # 同时存在的食物数量


class StepResult:
    """
    @brief Step结果结构体 - 强化学习环境的step()返回值
    
    Gym风格的step接口返回值, 包含执行动作后的完整信息。
    
    @note state_v: 新状态 (展平的tensor列表)
    @note reward_v: 获得的奖励
    @note terminal_v: 是否终止 (撞障碍物/出界/超时)
    
    @note 这是简化版, 只包含核心信息
    @note 完整版请参考 TransitionResult
    """
    __slots__ = ('state_v', 'reward_v', 'terminal_v')

    def __init__(self):
        """@brief 构造函数, 初始化所有属性为默认值"""
        self.state_v: list = []      # 新状态, 展平的tensor列表
        self.reward_v: float = 0.0   # 奖励值
        self.terminal_v: bool = False  # 是否终止


class Transition:
    """
    @brief 转换元组 - 存储(s, a, r, s', terminal)经验
    
    用于DQN的Experience Replay机制。
    每一个Transition表示智能体的一个经验: 在状态s执行动作a,
    获得奖励r, 到达状态s', 如果terminal=True则episode结束。
    
    @note state_v: 当前状态 (展平的tensor列表, 长度6534)
    @note action_v: 采取的动作 (0-8的整数)
    @note reward_v: 获得的奖励 (浮点数)
    @note next_state_v: 下一个状态 (展平的tensor列表)
    @note terminal_v: 是否终止 (布尔值)
    
    @example
        trans = Transition()
        trans.state_v = state_tensor
        trans.action_v = 3  # 向右下移动
        trans.reward_v = 1.5  # 吃到食物
        trans.next_state_v = next_state_tensor
        trans.terminal_v = False  # 继续
    """
    __slots__ = ('state_v', 'action_v', 'reward_v', 'next_state_v', 'terminal_v')

    def __init__(self):
        """
        @brief 构造函数
        
        初始化为空, 需要手动设置各个字段
        """
        self.state_v: list = []      # 当前状态
        self.action_v: int = 0       # 动作索引
        self.reward_v: float = 0.0   # 奖励值
        self.next_state_v: list = []  # 下一个状态
        self.terminal_v: bool = False  # 是否终止


class DQNConfig:
    """
    @brief DQN智能体配置结构体
    
    包含DQN算法的所有超参数。
    不同的超参数设置会影响学习效果和收敛速度。
    
    @note state_dim_v: 状态维度 (默认6*33*33=6534)
    @note action_dim_v: 动作维度 (默认9)
    @note learning_rate_v: 学习率, 控制梯度下降步长
    @note gamma_v: 折扣因子, 控制未来奖励的重要性
    @note epsilon_*: 探索率相关参数 (ε-greedy)
    @note batch_size_v: 批大小, 每次更新用的样本数
    @note memory_capacity_v: 经验池容量
    @note target_update_freq_v: 目标网络更新频率
    
    @example
        config = DQNConfig()
        config.learning_rate_v = 0.001  # 调整学习率
        config.gamma_v = 0.99          # 重视长期奖励
    """
    __slots__ = ('state_dim_v', 'action_dim_v', 'learning_rate_v', 'gamma_v',
                 'epsilon_start_v', 'epsilon_end_v', 'epsilon_decay_steps_v',
                 'batch_size_v', 'memory_capacity_v', 'target_update_freq_v')

    def __init__(self):
        """
        @brief 构造函数, 使用默认参数初始化
        """
        # 状态维度: 6通道 * 33 * 33 = 6534
        self.state_dim_v: int = K_CHANNEL_COUNT * K_WINDOW_SIZE * K_WINDOW_SIZE
        # 动作维度: 9个离散动作
        self.action_dim_v: int = K_ACTION_COUNT
        # 学习率: 控制模型更新的步长, 太大不稳定, 太小收敛慢
        self.learning_rate_v: float = 0.001
        # 折扣因子: gamma=0.99表示未来奖励占当前价值的99%
        self.gamma_v: float = 0.99
        # 初始探索率: 10%的概率随机选择动作 (探索)
        self.epsilon_start_v: float = 1.0
        # 最终探索率: 1%的概率随机选择动作 (利用已学知识)
        self.epsilon_end_v: float = 0.01
        # 探索率衰减步数: 10000步从1.0降到0.01
        self.epsilon_decay_steps_v: int = 10000
        # 批大小: 每次从经验池采样32个经验进行学习
        self.batch_size_v: int = 32
        # 经验池容量: 最多存储10000个经验, 超出则丢弃旧的
        self.memory_capacity_v: int = 10000
        # 目标网络更新频率: 每100步同步一次主网络到目标网络
        self.target_update_freq_v: int = 100
