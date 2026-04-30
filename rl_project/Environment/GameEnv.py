# -*- coding: utf-8 -*-
"""
@file GameEnv.py
@brief GameEnv 类 - 格子世界环境
@note 位于 rl_project/Environment/ 目录下

GameEnv是强化学习的核心环境类, 实现了标准的Gym风格的接口:
- reset(): 重置环境, 返回初始状态
- step(action): 执行动作, 返回(reward, terminal, info)

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
- 吃食物: +1.5 (含额外0.5鼓励)
- 撞障碍物: -1 (episode终止)
- 出界: -2 (episode终止)
- 靠近食物: +0.01 ~ +0.1 (取决于距离变化)
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
    
    实现了标准的强化学习环境接口, 供DQN/PPO智能体交互使用。
    
    @note config_v: 环境配置 (网格大小、障碍物概率等)
    @note grid_v: 64x64网格, 使用位掩码存储多层信息
    @note food_pos_list_v: 当前食物位置列表
    @note agent_pos_v: 智能体当前位置
    @note current_state_v: 当前状态 (State对象)
    @note t_v: 当前时间步
    @note total_reward_v: 当前episode累计奖励
    
    @example
        # 创建环境
        config = EnvConfig(height=32, width=32, obstacle_prob=0.03)
        env = GameEnv(config)
        
        # 重置环境
        state = env.reset()
        
        # 执行动作
        action = Action(0)  # 向上
        result = env.step(action)
        
        # 查看状态
        print(f"Reward: {result.reward_v}, Terminal: {result.terminal_v}")
    """
    # __slots__ 限制此类只能有这些属性, 减少内存占用
    __slots__ = ('config_v', 'grid_v', 'food_pos_list_v', 'agent_pos_v',
                 'current_state_v', 't_v', 'total_reward_v')

    def __init__(self, config: EnvConfig = None):
        """
        @brief 构造函数
        
        @param config: EnvConfig配置对象, 如果为None则使用默认配置
        
        @note 创建环境后自动调用reset()初始化状态
        
        @example
            # 使用默认配置
            env = GameEnv()
            
            # 使用自定义配置
            config = EnvConfig(height=32, width=32)
            env = GameEnv(config)
        """
        # 如果没有提供配置, 使用默认配置 (64x64, 5%障碍物概率)
        if config is None:
            config = EnvConfig()
        self.config_v: EnvConfig = config
        
        # 初始化网格 (高度 x 宽度), 每个格子用整数位掩码表示
        # 位掩码含义:
        # - bit 0 (1): Agent (智能体)
        # - bit 1 (2): Goal/Food (食物)
        # - bit 2 (4): Obstacle_N (北向障碍物)
        # - bit 3 (8): Obstacle_E (东向障碍物)
        # - bit 4 (16): Obstacle_S (南向障碍物)
        # - bit 5 (32): Obstacle_W (西向障碍物)
        # 一个格子可以同时有多个标记 (例如同时有食物和障碍物)
        self.grid_v: List[List[int]] = [[0] * config.width_v for _ in range(config.height_v)]
        
        # 食物位置列表, 存储当前所有食物的坐标
        self.food_pos_list_v: List[Position] = []
        
        # 智能体当前位置 (行, 列)
        self.agent_pos_v: Position = Position()
        
        # 当前状态 (State对象, 包含33x33窗口的tensor)
        self.current_state_v: State = State()
        
        # 当前时间步 (episode内的步数)
        self.t_v: int = 0
        
        # 当前episode累计奖励 (用于统计)
        self.total_reward_v: float = 0.0
        
        # 自动调用reset进行初始化
        self.reset()

    def reset(self) -> State:
        """
        @brief 重置环境到初始状态
        
        初始化一个新的episode:
        1. 清空网格和食物列表
        2. 随机放置智能体 (避开边界, 因为边界是障碍物通道)
        3. 生成障碍物和食物
        4. 重置时间步和奖励计数器
        5. 更新并返回初始状态
        
        @return 初始状态 (State对象, 包含状态tensor)
        
        @note 这是Gym风格接口的reset(), 每个episode开始时调用
        """
        # === 1. 清空网格 ===
        # 将所有格子重置为0 (无任何标记)
        for r in range(self.config_v.height_v):
            for c in range(self.config_v.width_v):
                self.grid_v[r][c] = 0
        
        # === 2. 清空食物列表 ===
        self.food_pos_list_v.clear()
        
        # === 3. 随机放置智能体 (避开边界) ===
        # 边界用于障碍物移动, 所以智能体不能放在边界上
        # 智能体位置范围: [1, height-2] x [1, width-2]
        self.agent_pos_v = Position(
            random.randint(1, self.config_v.height_v - 2),
            random.randint(1, self.config_v.width_v - 2)
        )
        
        # === 4. 生成障碍物和食物 ===
        self._generate_obstacles()  # 在四边生成障碍物
        self._generate_food()       # 生成食物
        
        # === 5. 重置计数器和状态 ===
        self.t_v = 0              # 时间步重置为0
        self.total_reward_v = 0.0  # 累计奖励重置为0
        
        # 更新当前状态 (创建State对象, 包含33x33窗口tensor)
        self._update_state()
        return self.current_state_v

    def _generate_obstacles(self) -> None:
        """
        @brief 在网格四边生成障碍物
        
        每个边缘有obstacle_prob_v的概率生成障碍物:
        - 上边(North edge): 生成S通道障碍物 (向南移动 -> 即从上方来)
        - 下边(South edge): 生成N通道障碍物 (向北移动 -> 即从下方来)
        - 左边(West edge): 生成E通道障碍物 (向西移动 -> 即从左边来)
        - 右边(East edge): 生成W通道障碍物 (向东移动 -> 即从右边来)
        
        @note 障碍物用bit位标记: bit 2=N, bit 3=E, bit 4=S, bit 5=W
        
        @note 障碍物不会放置在角角落, 以避免完全封死某个区域
        
        @example
            # 上边一格有障碍物: grid[0][c] |= (1 << K_OBSTACLE_S_CHANNEL)
            # 表示这个格子有向南移动的障碍物, 下一步会移动到grid[1][c]
        """
        # 遍历4条边 (0=上, 1=下, 2=左, 3=右)
        for edge in range(4):
            if edge == 0:
                # === 上边 (North edge) ===
                # 生成S通道障碍物 (bit 4)
                # 这些障碍物下一步会向下移动 (row + 1)
                for c in range(self.config_v.width_v):
                    if random.random() < self.config_v.obstacle_prob_v:
                        self.grid_v[0][c] |= (1 << K_OBSTACLE_S_CHANNEL)
                        
            elif edge == 1:
                # === 下边 (South edge) ===
                # 生成N通道障碍物 (bit 2)
                # 这些障碍物下一步会向上移动 (row - 1)
                for c in range(self.config_v.width_v):
                    if random.random() < self.config_v.obstacle_prob_v:
                        self.grid_v[self.config_v.height_v - 1][c] |= (1 << K_OBSTACLE_N_CHANNEL)
                        
            elif edge == 2:
                # === 左边 (West edge) ===
                # 生成E通道障碍物 (bit 3)
                # 这些障碍物下一步会向右移动 (col + 1)
                for r in range(self.config_v.height_v):
                    if random.random() < self.config_v.obstacle_prob_v:
                        self.grid_v[r][0] |= (1 << K_OBSTACLE_E_CHANNEL)
                        
            else:
                # === 右边 (East edge) ===
                # 生成W通道障碍物 (bit 5)
                # 这些障碍物下一步会向左移动 (col - 1)
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
        @note 吃食物后会在随机位置生成新食物, 保持食物数量恒定
        
        @example
            # 检查某格是否有食物: if grid[r][c] & (1 << K_GOAL_CHANNEL)
        """
        # 循环直到食物数量达到配置值
        while len(self.food_pos_list_v) < self.config_v.food_count_v:
            # 随机位置 (避开边界, 与智能体一样)
            pos = Position(
                random.randint(1, self.config_v.height_v - 2),
                random.randint(1, self.config_v.width_v - 2)
            )
            # 确保不与智能体重叠
            if not (pos.row_v == self.agent_pos_v.row_v and pos.col_v == self.agent_pos_v.col_v):
                # 添加到食物列表
                self.food_pos_list_v.append(pos)
                # 在网格中标记食物 (bit 1)
                self.grid_v[pos.row_v][pos.col_v] |= (1 << K_GOAL_CHANNEL)

    def _move_obstacles(self) -> None:
        """
        @brief 移动所有障碍物一格
        
        障碍物按其通道方向移动:
        - N通道(bit 2): row - 1 (向北移动)
        - E通道(bit 3): col + 1 (向东移动)
        - S通道(bit 4): row + 1 (向南移动)
        - W通道(bit 5): col - 1 (向西移动)
        
        移动后的位置如果超出网格则被丢弃 (被吸收)。
        
        @note 使用双缓冲网格避免在原地修改导致的问题
        @note 障碍物移动在step()的最后执行, 所以当前step看到的障碍物是上一步的位置
        
        @example
            # N通道障碍物从(5,5)移动到(4,5) (向北)
            # 如果目标位置超出网格(例如row<0), 则障碍物被移除
        """
        # === 创建新网格 (双缓冲) ===
        # 不能在原网格上直接修改, 否则会导致障碍物被移动多次
        new_grid = [[0] * self.config_v.width_v for _ in range(self.config_v.height_v)]
        
        # 障碍物移动方向映射
        # 索引对应: N(0), E(1), S(2), W(3)
        # K_OBSTACLE_N_CHANNEL = 2, 所以 dir_idx = ch - 2
        k_obstacle_move_row = (-1, 0, 1, 0)  # N: -1, E: 0, S: +1, W: 0
        k_obstacle_move_col = (0, 1, 0, -1)  # N: 0, E: +1, S: 0, W: -1
        
        # === 遍历网格, 移动有障碍物的格子 ===
        for r in range(self.config_v.height_v):
            for c in range(self.config_v.width_v):
                # 获取当前格子的所有标记
                cell = self.grid_v[r][c]
                
                # 检查每个障碍物通道 (2-5)
                for ch in range(K_OBSTACLE_N_CHANNEL, K_OBSTACLE_W_CHANNEL + 1):
                    # 检查当前格子是否有这个通道的障碍物
                    if cell & (1 << ch):
                        # 计算方向索引
                        # ch=2(N) -> dir_idx=0, ch=3(E) -> dir_idx=1, ...
                        dir_idx = ch - K_OBSTACLE_N_CHANNEL
                        
                        # 计算目标位置
                        dr = k_obstacle_move_row[dir_idx]
                        dc = k_obstacle_move_col[dir_idx]
                        new_r = r + dr
                        new_c = c + dc
                        
                        # 如果目标在网格内, 则移动; 否则丢弃
                        if new_r < self.config_v.height_v and new_c < self.config_v.width_v:
                            # 在新网格的目标位置设置同样的障碍物bit
                            new_grid[new_r][new_c] |= (1 << ch)
                        # 如果超出网格, 障碍物被移除 (相当于被吸收)
        
        # 用新网格替换旧网格
        self.grid_v = new_grid

    def _distance_to_nearest_food(self, pos: Position) -> float:
        """
        @brief 计算到最近食物的曼哈顿距离
        
        @param pos: 当前位置
        @return 到最近食物的曼哈顿距离, 如果没有食物则返回无穷大
        
        @note 使用曼哈顿距离 (|row1-row2| + |col1-col2|)
        @note 用于计算靠近食物的proximity reward
        """
        # 如果没有食物, 返回无穷大
        if not self.food_pos_list_v:
            return float('inf')
        
        # 找最近的的食物
        min_dist = float('inf')
        for food in self.food_pos_list_v:
            dist = abs(pos.row_v - food.row_v) + abs(pos.col_v - food.col_v)
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def step(self, action: Action) -> StepResult:
        """
        @brief 执行一个动作步骤
        
        标准的Gym风格step接口:
        1. 根据动作计算新位置
        2. 检查碰撞 (障碍物/边界)
        3. 处理食物收集和靠近奖励
        4. 更新障碍物
        5. 返回结果
        
        @param action: Action对象, 要执行的动作
        @return StepResult: 包含(reward, terminal)
        
        @note 如果terminal=True, 表示episode结束 (撞障碍物/出界)
        @note step后智能体看到的障碍物是上一步的位置, 不是当前位置的
        
        @example
            action = Action(0)  # 向上
            result = env.step(action)
            if result.terminal_v:
                print("Episode ended!")
            else:
                print(f"Got reward: {result.reward_v}")
        """
        # 创建返回结果对象
        result = StepResult()
        
        # === 1. 根据动作计算新位置 ===
        # 获取动作的方向向量 (例如 Action(0) 返回 Position(-1, 0))
        direction = action.direction()
        new_pos = Position(
            self.agent_pos_v.row_v + direction.row_v,
            self.agent_pos_v.col_v + direction.col_v
        )
        
        # === 计算移动前到最近食物的距离 (用于proximity reward) ===
        old_dist = self._distance_to_nearest_food(self.agent_pos_v)
        
        # === 2. 检查碰撞 ===
        
        # 检查是否出界 (边界不可达)
        # 边界位置: row=0, row=height-1, col=0, col=width-1
        if self._is_out_of_bounds(new_pos):
            result.reward_v = float(K_REWARD_OUT_OF_BOUNDS)  # -2
            result.terminal_v = True  # episode结束
            self.total_reward_v += result.reward_v
            self.t_v += 1
            return result
        
        # 检查是否撞到障碍物
        if self._is_obstacle(new_pos):
            result.reward_v = float(K_REWARD_OBSTACLE)  # -1
            result.terminal_v = True  # episode结束
            self.total_reward_v += result.reward_v
            self.t_v += 1
            return result
        
        # === 通过碰撞检查, 移动智能体到新位置 ===
        self.agent_pos_v = new_pos
        
        # === 3. 处理食物收集和靠近奖励 ===
        
        # 检查是否吃到食物
        if self._is_food(self.agent_pos_v):
            # 吃食物奖励 +1.5 (K_REWARD_FOOD=1 + 额外0.5)
            result.reward_v = float(K_REWARD_FOOD) + 0.5
            
            # 清除网格中的食物标记 (bit 1)
            self.grid_v[self.agent_pos_v.row_v][self.agent_pos_v.col_v] &= ~(1 << K_GOAL_CHANNEL)
            
            # 从食物列表移除
            for i, pos in enumerate(self.food_pos_list_v):
                if pos.row_v == self.agent_pos_v.row_v and pos.col_v == self.agent_pos_v.col_v:
                    self.food_pos_list_v.pop(i)
                    break
            
            # 生成新食物 (保持食物数量恒定)
            self._generate_food()
            
        else:
            # 没有吃食物, 检查是否靠近食物 (proximity reward)
            new_dist = self._distance_to_nearest_food(self.agent_pos_v)
            
            if new_dist < old_dist:
                # 靠近了食物, 给予正向奖励
                # 距离减少越多, 奖励越高, 最低0.05
                proximity_reward = max(0.05, (old_dist - new_dist) * 0.1)
                result.reward_v = float(proximity_reward)
            else:
                # 没有吃食物也没有靠近, 奖励为0
                result.reward_v = float(K_REWARD_DEFAULT)
        
        # === 4. 更新障碍物 ===
        
        # 定期重新生成边缘障碍物 (增加环境变化)
        if self.t_v % self.config_v.obstacle_freq_v == 0:
            self._generate_obstacles()
        
        # 移动所有障碍物一格
        self._move_obstacles()
        
        # === 5. 更新状态并返回 ===
        self._update_state()  # 更新current_state_v
        result.terminal_v = False  # 没有终止, 继续episode
        
        self.total_reward_v += result.reward_v
        self.t_v += 1  # 时间步增加
        
        return result

    def _is_out_of_bounds(self, pos: Position) -> bool:
        """
        @brief 检查位置是否在边界外
        
        @param pos: 要检查的位置
        @return True如果位置超出网格范围
        
        @note 边界定义: row<=0, row>=height-1, col<=0, col>=width-1
        @note 边界是不可达区域, 进入边界会导致episode结束
        """
        return (pos.row_v == 0 or pos.row_v >= self.config_v.height_v - 1 or
                pos.col_v == 0 or pos.col_v >= self.config_v.width_v - 1)

    def _is_obstacle(self, pos: Position) -> bool:
        """
        @brief 检查位置是否有障碍物
        
        @param pos: 要检查的位置
        @return True如果该位置有任意方向的障碍物
        
        @note 任何通道(bit 2-5)的障碍物都会返回True
        """
        # 边界外的位置视为无障碍 (避免误判)
        if not self._is_valid_pos(pos.row_v, pos.col_v):
            return False
        
        # 获取格子的所有标记
        cell = self.grid_v[pos.row_v][pos.col_v]
        
        # 检查是否有任何障碍物通道的标记
        for ch in range(K_OBSTACLE_N_CHANNEL, K_OBSTACLE_W_CHANNEL + 1):
            if cell & (1 << ch):
                return True
        return False

    def _is_food(self, pos: Position) -> bool:
        """
        @brief 检查位置是否有食物
        
        @param pos: 要检查的位置
        @return True如果该位置有食物
        
        @note 食物用bit 1 (K_GOAL_CHANNEL) 标记
        """
        # 边界外的位置视为无食物
        if not self._is_valid_pos(pos.row_v, pos.col_v):
            return False
        
        # 检查bit 1是否设置
        return (self.grid_v[pos.row_v][pos.col_v] & (1 << K_GOAL_CHANNEL)) != 0

    def _is_valid_pos(self, row: int, col: int) -> bool:
        """
        @brief 检查坐标是否在网格有效范围内
        
        @param row: 行坐标
        @param col: 列坐标
        @return True如果 0 <= row < height 且 0 <= col < width
        
        @note 用于避免数组越界访问
        """
        return row < self.config_v.height_v and col < self.config_v.width_v

    def _update_state(self) -> None:
        """
        @brief 更新当前状态
        
        根据当前环境创建一个新的State对象
        State包含33x33窗口的tensor, 作为神经网络的输入
        
        @note 每次step后需要调用此方法更新状态
        """
        self.current_state_v = State(self)

    def agent_pos(self) -> Position:
        """
        @brief 获取智能体当前位置
        
        @return Position对象, 表示智能体的(row, col)
        
        @example
            pos = env.agent_pos()
            print(f"Agent at ({pos.row_v}, {pos.col_v})")
        """
        return self.agent_pos_v

    def config(self) -> EnvConfig:
        """
        @brief 获取环境配置
        
        @return EnvConfig对象
        
        @example
            config = env.config()
            print(f"Grid size: {config.height_v}x{config.width_v}")
        """
        return self.config_v

    def current_state(self) -> State:
        """
        @brief 获取当前状态
        
        @return State对象, 包含状态tensor
        
        @note 返回值可以直接传给神经网络的forward()
        """
        return self.current_state_v

    def time_step(self) -> int:
        """
        @brief 获取当前时间步
        
        @return 当前episode内的步数
        
        @note 从0开始, 每次step后增加1
        """
        return self.t_v

    def total_reward(self) -> float:
        """
        @brief 获取当前episode累计奖励
        
        @return 累计奖励值
        
        @note 用于训练过程中的统计
        """
        return self.total_reward_v

    def grid(self):
        """
        @brief 获取网格数据
        
        @return 2D网格列表 [[int, ...], ...]
        
        @note 用于State初始化
        @note 每个格子是位掩码, 包含多个通道的信息
        """
        return self.grid_v

    def render(self) -> None:
        """
        @brief 渲染环境状态 (用于调试)
        
        打印当前环境的ASCII可视化:
        - A: 智能体位置
        - F: 食物位置
        - N/E/S/W: 各方向的障碍物
        - .: 空地
        
        @note 只显示左上角10x16区域, 避免输出过多
        """
        print("=== GameEnv Render ===")
        print(f"Time: {self.t_v}, Total Reward: {self.total_reward_v}")
        print(f"Agent Position: ({self.agent_pos_v.row_v}, {self.agent_pos_v.col_v})")
        print(f"Food Count: {len(self.food_pos_list_v)}")
        
        print("Grid (", end="")
        print()
        print(" ", end="")  # 行号前的空格
        
        # 只显示左上角区域 (10行 x 16列)
        for r in range(min(10, self.config_v.height_v)):
            if r > 0:
                print(" ", end="")  # 格式化对齐
            for c in range(min(16, self.config_v.width_v)):
                ch = '.'  # 默认空地
                
                # 检查智能体
                if r == self.agent_pos_v.row_v and c == self.agent_pos_v.col_v:
                    ch = 'A'
                # 检查食物 (bit 1)
                elif self.grid_v[r][c] & (1 << K_GOAL_CHANNEL):
                    ch = 'F'
                # 检查各方向障碍物 (bit 2-5)
                elif self.grid_v[r][c] & (1 << K_OBSTACLE_N_CHANNEL):
                    ch = 'N'
                elif self.grid_v[r][c] & (1 << K_OBSTACLE_E_CHANNEL):
                    ch = 'E'
                elif self.grid_v[r][c] & (1 << K_OBSTACLE_S_CHANNEL):
                    ch = 'S'
                elif self.grid_v[r][c] & (1 << K_OBSTACLE_W_CHANNEL):
                    ch = 'W'
                    
                print(ch, end="")
            print()  # 换行
        print("=== End Render ===")
