# -*- coding: utf-8 -*-
"""
@file State.py
@brief State 类 - 智能体的感知状态
@note 位于 rl_project/python/Environment/ 目录下

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

    状态以33x33窗口形式呈现, 包含6个通道, 共6534维特征.
    使用__slots__优化内存, 避免动态属性创建.

    @note tensor_v: 展平的状态向量 [6 * 33 * 33], 类型为List[float]

    @example
        state = State(env)  # 从环境创建状态
        tensor = state.tensor()  # 获取状态tensor
    """
    __slots__ = ('tensor_v',)

    def __init__(self, env=None):
        """
        @brief 构造函数

        @param env: GameEnv实例, 如果为None则创建空状态

        @note 如果提供了env, 会自动调用_initialize_from_env初始化状态
        """
        # 初始化展平的tensor: 6通道 * 33 * 33 = 6534维
        self.tensor_v: List[float] = [0.0] * (K_CHANNEL_COUNT * K_WINDOW_SIZE * K_WINDOW_SIZE)
        if env is not None:
            self._initialize_from_env(env)

    def _initialize_from_env(self, env) -> None:
        """
        @brief 从游戏环境初始化状态tensor

        创建以智能体为中心的33x33窗口状态表示:
        1. 初始化所有位置为0.5 (表示未知/不可见)
        2. 遍历环境网格, 将可见的智能体、食物、障碍物位置标记到对应通道
        3. 只标记在33x33窗口范围内的物体
        4. 将3D channel_data展平为1D tensor

        @param env: GameEnv游戏环境实例
        """
        # 获取环境和智能体信息
        config = env.config()
        agent_pos = env.agent_pos()
        grid = env.grid()

        # 计算以智能体为中心的窗口边界
        # 窗口范围: [agent_row - 16, agent_row + 16]
        window_min_row = agent_pos.row_v - K_HALF_SIZE
        window_max_row = agent_pos.row_v + K_HALF_SIZE + 1
        window_min_col = agent_pos.col_v - K_HALF_SIZE
        window_max_col = agent_pos.col_v + K_HALF_SIZE + 1

        # 创建3D channel数据 [6][33][33], 初始值为0.5
        channel_data = [[[0.5 for _ in range(K_WINDOW_SIZE)] for _ in range(K_WINDOW_SIZE)] for _ in range(K_CHANNEL_COUNT)]

        # 遍历环境网格 (64x64)
        for r in range(config.height_v):
            for c in range(config.width_v):
                # 检查是否在窗口范围内
                if not (window_min_row <= r < window_max_row and window_min_col <= c < window_max_col):
                    continue

                # 计算在33x33窗口中的位置
                target_r = r - window_min_row
                target_c = c - window_min_col

                # 获取该格子的所有信息
                cell = grid[r][c]

                # 检查是否是智能体位置 (优先级最高)
                if r == agent_pos.row_v and c == agent_pos.col_v:
                    channel_data[K_AGENT_CHANNEL][target_r][target_c] = 1.0

                # 检查是否有食物
                if cell & (1 << K_GOAL_CHANNEL):
                    channel_data[K_GOAL_CHANNEL][target_r][target_c] = 1.0

                # 检查各个方向的障碍物
                if cell & (1 << K_OBSTACLE_N_CHANNEL):
                    channel_data[K_OBSTACLE_N_CHANNEL][target_r][target_c] = 1.0
                if cell & (1 << K_OBSTACLE_E_CHANNEL):
                    channel_data[K_OBSTACLE_E_CHANNEL][target_r][target_c] = 1.0
                if cell & (1 << K_OBSTACLE_S_CHANNEL):
                    channel_data[K_OBSTACLE_S_CHANNEL][target_r][target_c] = 1.0
                if cell & (1 << K_OBSTACLE_W_CHANNEL):
                    channel_data[K_OBSTACLE_W_CHANNEL][target_r][target_c] = 1.0

        # 将3D channel数据 [6][33][33] 展平为1D tensor [6534]
        # 格式: [ch0*1089, ch1*1089, ..., ch5*1089]
        idx = 0
        for ch in range(K_CHANNEL_COUNT):
            for r in range(K_WINDOW_SIZE):
                for c in range(K_WINDOW_SIZE):
                    self.tensor_v[idx] = channel_data[ch][r][c]
                    idx += 1

    def tensor(self) -> List[float]:
        """
        @brief 获取状态tensor

        @return 展平的状态向量 (List[float], 长度6534)
        """
        return self.tensor_v

    @staticmethod
    def window_size() -> int:
        """
        @brief 获取窗口大小

        @return 窗口边长 (33)
        """
        return K_WINDOW_SIZE

    @staticmethod
    def channel_count() -> int:
        """
        @brief 获取通道数量

        @return 通道数 (6)
        """
        return K_CHANNEL_COUNT