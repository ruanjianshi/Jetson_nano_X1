# -*- coding: utf-8 -*-
"""
@file Action.py
@brief Action 类 - 智能体的动作
@note 位于 rl_project/python/Environment/ 目录下

Action类表示智能体可以采取的离散动作。

## 动作空间 (Action Space)

智能体有9个可选动作, 包括8个方向移动和1个原地不动:

    7  0  1      ↖ ↑ ↗
    6  8  2      ← □ →     <- 用字符表示
    5  4  3      ↙ ↓ ↘

每个动作对应一个方向向量 (d_row, d_col):
- 0 (↑):  (-1,  0)  - 向上
- 1 (↗):  (-1,  1)  - 向右上
- 2 (→):  ( 0,  1)  - 向右
- 3 (↘):  ( 1,  1)  - 向右下
- 4 (↓):  ( 1,  0)  - 向下
- 5 (↙):  ( 1, -1)  - 向左下
- 6 (←):  ( 0, -1)  - 向左
- 7 (↖):  (-1, -1)  - 向左上
- 8 (□):  ( 0,  0)  - 原地不动
"""

from Utils.types import K_ACTION_COUNT, K_ACTION_CHARS, K_DIRECTION_ROW, K_DIRECTION_COL, Position


class Action:
    """
    @brief 动作类 - 表示智能体的离散动作选择
    
    动作用索引0-8表示, 每个动作对应一个移动方向.
    使用__slots__优化内存占用.
    
    @note index_v: 动作索引 [0, 8]
    
    @example
        action = Action(0)      # 创建向上动作
        action = Action.random()  # 随机动作
        print(action.to_string()) # 打印 "↑"
        print(action.direction()) # 打印 Position(-1, 0)
    """
    __slots__ = ('index_v',)

    def __init__(self, action_idx: int = 0):
        """
        @brief 构造函数
        
        @param action_idx: 动作索引 [0, 8], 超出范围则设为8 (原地不动)
        """
        # 边界检查: 确保索引在有效范围内 [0, 8]
        self.index_v: int = action_idx if action_idx < K_ACTION_COUNT else 8

    @staticmethod
    def random() -> 'Action':
        """
        @brief 创建随机动作
        
        @return 随机选择的Action实例
        """
        import random
        return Action(random.randint(0, K_ACTION_COUNT - 1))

    @staticmethod
    def from_index(idx: int) -> 'Action':
        """
        @brief 从索引创建动作
        
        @param idx: 动作索引
        @return Action实例
        """
        return Action(idx)

    def index(self) -> int:
        """
        @brief 获取动作索引
        
        @return 动作索引 [0, 8]
        """
        return self.index_v

    def to_string(self) -> str:
        """
        @brief 获取动作的Unicode字符表示
        
        @return 动作字符, 如 "↑", "↗", "□" 等
        """
        return K_ACTION_CHARS[self.index_v]

    def direction(self) -> Position:
        """
        @brief 获取动作对应的方向向量
        
        @return Position对象, 表示(row_offset, col_offset)
        
        @example
            action = Action(0)  # UP
            pos = action.direction()  # Position(-1, 0)
            # 如果智能体在(10, 10), 执行动作后移动到(9, 10)
        """
        return Position(K_DIRECTION_ROW[self.index_v], K_DIRECTION_COL[self.index_v])