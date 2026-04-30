# -*- coding: utf-8 -*-
"""
@file State.py
@brief State 类 - 智能体的感知状态
@note 位于 rl_project/Environment/ 目录下

State类负责将游戏环境转换为智能体可以使用的状态表示。

## 状态表示 (State Representation)

智能体观测到的状态是一个以自身为中心的33x33窗口, 包含6个通道:

Channel 0 (Agent):    智能体位置 -> 1.0
Channel 1 (Goal):    食物位置 -> 1.0
Channel 2 (Obs_N):   北向障碍物 -> 1.0
Channel 3 (Obs_E):   东向障碍物 -> 1.0
Channel 4 (Obs_S):   南向障碍物 -> 1.0
Channel 5 (Obs_W):   西向障碍物 -> 1.0

其余位置用0.5填充 (表示"未知"或"不可见"区域)。

## Padding策略

由于智能体位于64x64的网格中, 而观测窗口只有33x33,
因此需要在四周填充17圈0.5来表示边界外的"未知"区域。
"""

from typing import List
from Utils.types import (
    K_WINDOW_SIZE, K_HALF_SIZE, K_CHANNEL_COUNT,
    K_AGENT_CHANNEL, K_GOAL_CHANNEL,
    K_OBSTACLE_N_CHANNEL, K_OBSTACLE_E_CHANNEL,
    K_OBSTACLE_S_CHANNEL, K_OBSTACLE_W_CHANNEL
)


class State:
    """
    @brief 状态类 - 将游戏环境转换为神经网络输入
    
    状态以33x33窗口形式呈现, 包含6个通道, 共6534维特征。
    使用__slots__优化内存, 避免动态属性创建。
    
    @note tensor_v: 展平的状态向量 [6 * 33 * 33], 类型为List[float]
    
    @example
        # 从环境创建状态
        state = State(env)
        
        # 获取状态tensor (用于神经网络输入)
        tensor = state.tensor()  # 返回 [6534] 的list
        
        # 查看窗口大小
        size = State.window_size()  # 返回 33
    """
    # __slots__ 限制此类只能有tensor_v一个属性, 减少内存占用
    __slots__ = ('tensor_v',)

    def __init__(self, env=None):
        """
        @brief 构造函数
        
        @param env: GameEnv实例, 如果为None则创建空状态
        
        @note 如果提供了env, 会自动调用_initialize_from_env初始化状态
        @note 如果没有提供env, 状态tensor初始化为全0
        
        @example
            # 从环境创建状态
            state = State(env)
            
            # 创建空状态
            state = State()
        """
        # 初始化展平的tensor: 6通道 * 33 * 33 = 6534维
        # 初始值为0.0, 后续会通过_initialize_from_env填充
        self.tensor_v: List[float] = [0.0] * (K_CHANNEL_COUNT * K_WINDOW_SIZE * K_WINDOW_SIZE)
        
        # 如果提供了环境, 从环境初始化状态
        if env is not None:
            self._initialize_from_env(env)

    def _initialize_from_env(self, env) -> None:
        """
        @brief 从游戏环境初始化状态tensor
        
        创建以智能体为中心的33x33窗口状态表示:
        1. 初始化所有位置为0.5 (表示未知/不可见区域)
        2. 遍历环境网格, 将可见的智能体、食物、障碍物位置标记到对应通道
        3. 只标记在33x33窗口范围内的物体
        4. 将3D channel_data展平为1D tensor
        
        @param env: GameEnv游戏环境实例
        
        @note 使用0.5填充而非0, 是因为:
        - 0表示"确认没有某物"
        - 0.5表示"未知/不可见"
        - 这样神经网络可以区分"看到空无一物"和"没有视野"
        
        @note 展平顺序: 按通道顺序, 每个通道内按行优先
        - self.tensor_v[0:1089] = Channel 0 (Agent)
        - self.tensor_v[1089:2178] = Channel 1 (Goal)
        - self.tensor_v[2178:3267] = Channel 2 (Obs_N)
        - self.tensor_v[3267:4356] = Channel 3 (Obs_E)
        - self.tensor_v[4356:5445] = Channel 4 (Obs_S)
        - self.tensor_v[5445:6534] = Channel 5 (Obs_W)
        """
        # 获取环境和智能体信息
        config = env.config()           # 环境配置 (网格大小等)
        agent_pos = env.agent_pos()     # 智能体当前位置
        grid = env.grid()              # 环境的2D网格
        
        # 计算以智能体为中心的窗口边界
        # 例如: 如果智能体在(50, 50), 窗口范围是[34, 67)
        # K_HALF_SIZE = 16, 所以窗口是 [pos-16, pos+16+1) = [34, 67)
        window_min_row = agent_pos.row_v - K_HALF_SIZE
        window_max_row = agent_pos.row_v + K_HALF_SIZE + 1  # +1因为Python的range是左闭右开
        window_min_col = agent_pos.col_v - K_HALF_SIZE
        window_max_col = agent_pos.col_v + K_HALF_SIZE + 1
        
        # 创建3D channel数据 [6][33][33], 初始值为0.5 (未知区域)
        # channel_data[channel][row][col] = 值 (0.0, 0.5, 或 1.0)
        # 0.0 = 确认没有某物, 0.5 = 未知/不可见, 1.0 = 确认有某物
        channel_data = [[[0.5 for _ in range(K_WINDOW_SIZE)] for _ in range(K_WINDOW_SIZE)] for _ in range(K_CHANNEL_COUNT)]
        
        # 遍历环境网格 (例如64x64)
        # 只处理在窗口范围内的格子
        for r in range(config.height_v):
            for c in range(config.width_v):
                # 检查当前格子是否在窗口范围内
                # 不在窗口范围内的格子不会被编码到状态中
                if not (window_min_row <= r < window_max_row and window_min_col <= c < window_max_col):
                    continue
                
                # 计算当前格子在33x33窗口中的位置
                # 例如: 窗口min是34, 如果格子在37行, 则窗口内位置是37-34=3
                target_r = r - window_min_row
                target_c = c - window_min_col
                
                # 获取该格子的所有信息 (位掩码)
                cell = grid[r][c]
                
                # === 标记智能体位置 (Channel 0) ===
                # 智能体位置标记为1.0, 优先级最高
                # 因为智能体总是位于窗口中心附近
                if r == agent_pos.row_v and c == agent_pos.col_v:
                    channel_data[K_AGENT_CHANNEL][target_r][target_c] = 1.0
                
                # === 标记食物/目标位置 (Channel 1) ===
                # 检查该格子是否有食物 (通过Goal Channel的bit位)
                # K_GOAL_CHANNEL = 1, 对应grid[r][c]的bit 1
                if cell & (1 << K_GOAL_CHANNEL):
                    channel_data[K_GOAL_CHANNEL][target_r][target_c] = 1.0
                
                # === 标记障碍物位置 (Channel 2-5) ===
                # 每个方向的障碍物有不同的bit位和移动方向:
                # - Obs_N (bit 2): 从北向南移动, 即障碍物来自北方
                # - Obs_E (bit 3): 从东向西移动, 即障碍物来自东方
                # - Obs_S (bit 4): 从南向北移动, 即障碍物来自南方
                # - Obs_W (bit 5): 从西向东移动, 即障碍物来自西方
                if cell & (1 << K_OBSTACLE_N_CHANNEL):
                    channel_data[K_OBSTACLE_N_CHANNEL][target_r][target_c] = 1.0
                if cell & (1 << K_OBSTACLE_E_CHANNEL):
                    channel_data[K_OBSTACLE_E_CHANNEL][target_r][target_c] = 1.0
                if cell & (1 << K_OBSTACLE_S_CHANNEL):
                    channel_data[K_OBSTACLE_S_CHANNEL][target_r][target_c] = 1.0
                if cell & (1 << K_OBSTACLE_W_CHANNEL):
                    channel_data[K_OBSTACLE_W_CHANNEL][target_r][target_c] = 1.0
        
        # === 将3D channel数据 [6][33][33] 展平为1D tensor [6534] ===
        # 展平顺序: 按通道优先, 每个通道内按行优先
        # self.tensor_v[0:1089] = Channel 0 (Agent)
        # self.tensor_v[1089:2178] = Channel 1 (Goal)
        # ...
        idx = 0  # tensor_v的当前索引
        for ch in range(K_CHANNEL_COUNT):           # 遍历6个通道
            for r in range(K_WINDOW_SIZE):          # 遍历33行
                for c in range(K_WINDOW_SIZE):      # 遍历33列
                    self.tensor_v[idx] = channel_data[ch][r][c]
                    idx += 1

    def tensor(self) -> List[float]:
        """
        @brief 获取状态tensor
        
        @return 展平的状态向量 (List[float], 长度6534)
        
        @note 返回值可以直接作为神经网络输入
        @note 格式: [6*33*33] = [Channel0, Channel1, ..., Channel5]
        
        @example
            state = State(env)
            tensor = state.tensor()  # 获取状态tensor
            # tensor长度 = 6534
            # tensor[0:1089] = Agent通道
            # tensor[1089:2178] = Goal通道
            # ...
        """
        return self.tensor_v

    @staticmethod
    def window_size() -> int:
        """
        @brief 获取窗口大小
        
        @return 窗口边长 (33)
        
        @note 静态方法, 无需创建State实例即可调用
        
        @example
            size = State.window_size()  # 返回 33
        """
        return K_WINDOW_SIZE

    @staticmethod
    def channel_count() -> int:
        """
        @brief 获取通道数量
        
        @return 通道数 (6)
        
        @note 静态方法, 无需创建State实例即可调用
        @note 6个通道: Agent(0), Goal(1), Obs_N(2), Obs_E(3), Obs_S(4), Obs_W(5)
        
        @example
            count = State.channel_count()  # 返回 6
        """
        return K_CHANNEL_COUNT
