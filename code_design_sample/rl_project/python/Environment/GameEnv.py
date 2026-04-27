# -*- coding: utf-8 -*-
"""
@file GameEnv.py
@brief GameEnv 类 - 格子世界环境
@note 位于 rl_project/python/Environment/ 目录下

GameEnv是强化学习的核心环境类, 实现了标准的Gym风格的接口:
- reset(): 重置环境, 返回初始状态
- step(action): 执行动作, 返回(next_state, reward, terminal, info)

## 环境设计

### 网格结构 (Grid Structure)
- 默认64x64的二维网格
- 网格使用位掩码(Bitmask)存储多layer信息:
  - bit 0: Agent (智能体)
  - bit 1: Goal/Food (食物)
  - bit 2-5: Obstacles (4个方向的障碍物)

### 障碍物系统 (Obstacle System)
- 障碍物沿网格四边生成 (上/下/左/右边缘)
- 每隔obstacle_freq步重新生成边缘障碍物
- 障碍物每步向其对应方向移动一格
  - N通道障碍物: 向南(下)移动
  - E通道障碍物: 向西(左)移动
  - S通道障碍物: 向北(上)移动
  - W通道障碍物: 向东(右)移动

### 食物系统 (Food System)
- 初始生成food_count个食物
- 智能体吃到食物后, 该食物消失并立即在随机位置生成新食物
- 食物位置用Goal Channel标记

### 奖励机制 (Reward System)
- 吃食物: +1
- 撞障碍物: -1 (episode终止)
- 出界: -2 (episode终止)
- 其他: 0

### 状态空间 (State Space)
- 智能体观测: 以自身为中心的33x33窗口
- 6通道tensor: [Agent, Goal, Obs_N, Obs_E, Obs_S, Obs_W]
- 状态维度: 6 * 33 * 33 = 6534
"""

import random
from typing import List
from Utils.types import (
    EnvConfig, Position, TransitionResult, StepResult,
    K_CHANNEL_COUNT, K_WINDOW_SIZE, K_HALF_SIZE,
    K_AGENT_CHANNEL, K_GOAL_CHANNEL, K_OBSTACLE_N_CHANNEL,
    K_OBSTACLE_E_CHANNEL, K_OBSTACLE_S_CHANNEL, K_OBSTACLE_W_CHANNEL,
    K_REWARD_FOOD, K_REWARD_OBSTACLE, K_REWARD_OUT_OF_BOUNDS, K_REWARD_DEFAULT
)
from Environment.State import State
from Environment.Action import Action


class GameEnv:
    """
    @brief 格子世界环境类 - 强化学习环境实现

    实现了标准的强化学习环境接口, 供DQN智能体交互使用.

    @note config_v: 环境配置
    @note grid_v: 64x64网格, 使用位掩码存储多层信息
    @note food_pos_list_v: 当前食物位置列表
    @note agent_pos_v: 智能体当前位置
    @note current_state_v: 当前状态 (State对象)
    @note t_v: 当前时间步
    @note total_reward_v: 当前episode累计奖励
    """
    __slots__ = ('config_v', 'grid_v', 'food_pos_list_v', 'agent_pos_v',
                 'current_state_v', 't_v', 'total_reward_v')

    def __init__(self, config: EnvConfig = None):
        """
        @brief 构造函数

        @param config: EnvConfig配置对象, 如果为None则使用默认配置
        """
        if config is None:
            config = EnvConfig()
        self.config_v: EnvConfig = config

        # 初始化网格 (高度 x 宽度), 每个格子用整数位掩码表示
        self.grid_v: List[List[int]] = [[0] * config.width_v for _ in range(config.height_v)]
        self.food_pos_list_v: List[Position] = []      # 食物位置列表
        self.agent_pos_v: Position = Position()        # 智能体位置
        self.current_state_v: State = State()           # 当前状态
        self.t_v: int = 0                              # 时间步
        self.total_reward_v: float = 0.0               # 累计奖励

        # 自动调用reset进行初始化
        self.reset()

    def reset(self) -> State:
        """
        @brief 重置环境到初始状态

        1. 清空网格和食物列表
        2. 随机放置智能体 (避开边界)
        3. 生成障碍物和食物
        4. 重置时间步和奖励计数器
        5. 更新并返回初始状态

        @return 初始状态 (State对象)
        """
        # 清空网格
        for r in range(self.config_v.height_v):
            for c in range(self.config_v.width_v):
                self.grid_v[r][c] = 0

        # 清空食物列表
        self.food_pos_list_v.clear()

        # 随机放置智能体 (避开边界, 边界用于移动障碍物)
        self.agent_pos_v = Position(
            random.randint(1, self.config_v.height_v - 2),
            random.randint(1, self.config_v.width_v - 2)
        )

        # 生成障碍物和食物
        self._generate_obstacles()
        self._generate_food()

        # 重置计数器和状态
        self.t_v = 0
        self.total_reward_v = 0.0

        self._update_state()
        return self.current_state_v

    def _generate_obstacles(self) -> None:
        """
        @brief 在网格四边生成障碍物

        每个边缘有obstacle_prob_v的概率生成障碍物:
        - 上边(North edge): 生成S通道障碍物 (向北移动 -> 即从上方来)
        - 下边(South edge): 生成N通道障碍物 (向南移动 -> 即从下方来)
        - 左边(West edge): 生成E通道障碍物 (向西移动 -> 即从左边来)
        - 右边(East edge): 生成W通道障碍物 (向东移动 -> 即从右边来)

        @note 障碍物用bit位标记: bit 2=N, bit 3=E, bit 4=S, bit 5=W
        """
        for edge in range(4):
            if edge == 0:  # 上边 - 生成向南移动的障碍物
                for c in range(self.config_v.width_v):
                    if random.random() < self.config_v.obstacle_prob_v:
                        self.grid_v[0][c] |= (1 << K_OBSTACLE_S_CHANNEL)
            elif edge == 1:  # 下边 - 生成向北移动的障碍物
                for c in range(self.config_v.width_v):
                    if random.random() < self.config_v.obstacle_prob_v:
                        self.grid_v[self.config_v.height_v - 1][c] |= (1 << K_OBSTACLE_N_CHANNEL)
            elif edge == 2:  # 左边 - 生成向东移动的障碍物
                for r in range(self.config_v.height_v):
                    if random.random() < self.config_v.obstacle_prob_v:
                        self.grid_v[r][0] |= (1 << K_OBSTACLE_E_CHANNEL)
            else:  # 右边 - 生成向西移动的障碍物
                for r in range(self.config_v.height_v):
                    if random.random() < self.config_v.obstacle_prob_v:
                        self.grid_v[r][self.config_v.width_v - 1] |= (1 << K_OBSTACLE_W_CHANNEL)

    def _generate_food(self) -> None:
        """
        @brief 生成食物

        持续生成食物直到达到配置的食物数量:
        - 在网格内随机选择位置 (避开边界)
        - 确保不与智能体位置重叠

        @note 食物位置用bit 1 (K_GOAL_CHANNEL) 标记
        """
        while len(self.food_pos_list_v) < self.config_v.food_count_v:
            pos = Position(
                random.randint(1, self.config_v.height_v - 2),
                random.randint(1, self.config_v.width_v - 2)
            )
            # 确保不与智能体重叠
            if not (pos.row_v == self.agent_pos_v.row_v and pos.col_v == self.agent_pos_v.col_v):
                self.food_pos_list_v.append(pos)
                self.grid_v[pos.row_v][pos.col_v] |= (1 << K_GOAL_CHANNEL)

    def _move_obstacles(self) -> None:
        """
        @brief 移动所有障碍物一格

        障碍物按其通道方向移动:
        - N通道: row - 1 (向北)
        - E通道: col + 1 (向东)
        - S通道: row + 1 (向南)
        - W通道: col - 1 (向西)

        移动后的位置如果超出网格则丢弃 (被吸收).

        @note 使用双缓冲网格避免原地修改问题
        """
        # 创建新网格 (双缓冲)
        new_grid = [[0] * self.config_v.width_v for _ in range(self.config_v.height_v)]

        # 障碍物移动方向映射
        k_obstacle_move_row = (-1, 0, 1, 0)  # N, E, S, W
        k_obstacle_move_col = (0, 1, 0, -1)

        # 遍历网格, 移动有障碍物的格子
        for r in range(self.config_v.height_v):
            for c in range(self.config_v.width_v):
                cell = self.grid_v[r][c]

                # 检查每个障碍物通道
                for ch in range(K_OBSTACLE_N_CHANNEL, K_OBSTACLE_W_CHANNEL + 1):
                    if cell & (1 << ch):
                        # 计算方向索引和目标位置
                        dir_idx = ch - K_OBSTACLE_N_CHANNEL
                        dr = k_obstacle_move_row[dir_idx]
                        dc = k_obstacle_move_col[dir_idx]

                        new_r = r + dr
                        new_c = c + dc

                        # 如果目标在网格内, 则移动
                        if new_r < self.config_v.height_v and new_c < self.config_v.width_v:
                            new_grid[new_r][new_c] |= (1 << ch)

        self.grid_v = new_grid

    def step(self, action: Action) -> StepResult:
        """
        @brief 执行一个动作步骤

        标准的Gym风格step接口:
        1. 根据动作计算新位置
        2. 检查碰撞 (障碍物/边界)
        3. 处理食物收集
        4. 更新障碍物
        5. 返回结果

        @param action: Action对象, 要执行的动作
        @return StepResult: 包含(next_state, reward, terminal)

        @note 如果terminal=True, 表示episode结束
        """
        result = StepResult()

        # 计算新位置
        direction = action.direction()
        new_pos = Position(
            self.agent_pos_v.row_v + direction.row_v,
            self.agent_pos_v.col_v + direction.col_v
        )

        # 检查是否出界 (边界不可达)
        if self._is_out_of_bounds(new_pos):
            result.reward_v = float(K_REWARD_OUT_OF_BOUNDS)
            result.terminal_v = True
            self.total_reward_v += result.reward_v
            self.t_v += 1
            return result

        # 检查是否撞到障碍物
        if self._is_obstacle(new_pos):
            result.reward_v = float(K_REWARD_OBSTACLE)
            result.terminal_v = True
            self.total_reward_v += result.reward_v
            self.t_v += 1
            return result

        # 移动智能体到新位置
        self.agent_pos_v = new_pos

        # 检查是否吃到食物
        if self._is_food(self.agent_pos_v):
            result.reward_v = float(K_REWARD_FOOD)
            # 清除食物标记
            self.grid_v[self.agent_pos_v.row_v][self.agent_pos_v.col_v] &= ~(1 << K_GOAL_CHANNEL)
            # 从食物列表移除
            for i, pos in enumerate(self.food_pos_list_v):
                if pos.row_v == self.agent_pos_v.row_v and pos.col_v == self.agent_pos_v.col_v:
                    self.food_pos_list_v.pop(i)
                    break
            # 生成新食物
            self._generate_food()
        else:
            result.reward_v = float(K_REWARD_DEFAULT)

        # 定期重新生成边缘障碍物
        if self.t_v % self.config_v.obstacle_freq_v == 0:
            self._generate_obstacles()

        # 移动障碍物
        self._move_obstacles()

        # 更新状态
        self._update_state()
        result.terminal_v = False

        self.total_reward_v += result.reward_v
        self.t_v += 1

        return result

    def _is_out_of_bounds(self, pos: Position) -> bool:
        """
        @brief 检查位置是否在边界外

        @return True如果位置超出网格范围 (row<=0, row>=height-1, col<=0, col>=width-1)
        """
        return (pos.row_v == 0 or pos.row_v >= self.config_v.height_v - 1 or
                pos.col_v == 0 or pos.col_v >= self.config_v.width_v - 1)

    def _is_obstacle(self, pos: Position) -> bool:
        """
        @brief 检查位置是否有障碍物

        @return True如果该位置有任意方向的障碍物
        """
        if not self._is_valid_pos(pos.row_v, pos.col_v):
            return False
        cell = self.grid_v[pos.row_v][pos.col_v]
        for ch in range(K_OBSTACLE_N_CHANNEL, K_OBSTACLE_W_CHANNEL + 1):
            if cell & (1 << ch):
                return True
        return False

    def _is_food(self, pos: Position) -> bool:
        """
        @brief 检查位置是否有食物

        @return True如果该位置有食物 (Goal Channel)
        """
        if not self._is_valid_pos(pos.row_v, pos.col_v):
            return False
        return (self.grid_v[pos.row_v][pos.col_v] & (1 << K_GOAL_CHANNEL)) != 0

    def _is_valid_pos(self, row: int, col: int) -> bool:
        """
        @brief 检查坐标是否在网格有效范围内

        @return True如果 0 <= row < height 且 0 <= col < width
        """
        return row < self.config_v.height_v and col < self.config_v.width_v

    def _update_state(self) -> None:
        """
        @brief 更新当前状态

        根据当前环境创建一个新的State对象
        """
        self.current_state_v = State(self)

    def agent_pos(self) -> Position:
        """@brief 获取智能体当前位置"""
        return self.agent_pos_v

    def config(self) -> EnvConfig:
        """@brief 获取环境配置"""
        return self.config_v

    def current_state(self) -> State:
        """@brief 获取当前状态"""
        return self.current_state_v

    def time_step(self) -> int:
        """@brief 获取当前时间步"""
        return self.t_v

    def total_reward(self) -> float:
        """@brief 获取当前episode累计奖励"""
        return self.total_reward_v

    def grid(self):
        """@brief 获取网格数据 (用于State初始化)"""
        return self.grid_v

    def render(self) -> None:
        """
        @brief 渲染环境状态 (用于调试)

        打印当前环境的可视化的ASCII表示:
        - A: 智能体位置
        - F: 食物位置
        - N/E/S/W: 各方向的障碍物
        - .: 空地
        """
        print("=== GameEnv Render ===")
        print(f"Time: {self.t_v}, Total Reward: {self.total_reward_v}")
        print(f"Agent Position: ({self.agent_pos_v.row_v}, {self.agent_pos_v.col_v})")
        print(f"Food Count: {len(self.food_pos_list_v)}")

        print("Grid (", end="")
        for r in range(min(10, self.config_v.height_v)):
            if r > 0:
                print(" ", end="")
            for c in range(min(16, self.config_v.width_v)):
                ch = '.'
                if r == self.agent_pos_v.row_v and c == self.agent_pos_v.col_v:
                    ch = 'A'
                elif self.grid_v[r][c] & (1 << K_GOAL_CHANNEL):
                    ch = 'F'
                elif self.grid_v[r][c] & (1 << K_OBSTACLE_N_CHANNEL):
                    ch = 'N'
                elif self.grid_v[r][c] & (1 << K_OBSTACLE_E_CHANNEL):
                    ch = 'E'
                elif self.grid_v[r][c] & (1 << K_OBSTACLE_S_CHANNEL):
                    ch = 'S'
                elif self.grid_v[r][c] & (1 << K_OBSTACLE_W_CHANNEL):
                    ch = 'W'
                print(ch, end="")
            print()
        print("=== End Render ===")