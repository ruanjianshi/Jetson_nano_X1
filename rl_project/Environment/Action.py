# -*- coding: utf-8 -*-
"""
@file Action.py
@brief Action 类 - 智能体的动作
@note 位于 rl_project/Environment/ 目录下

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
    
    动作用索引0-8表示, 每个动作对应一个移动方向。
    使用__slots__优化内存占用, 避免动态字典创建。
    
    @note index_v: 动作索引 [0, 8]
    - 0-7: 8个方向移动
    - 8: 原地不动
    
    @example
        # 创建动作
        action = Action(0)       # 创建向上动作
        action = Action(3)      # 创建向右下动作
        
        # 随机动作
        action = Action.random()
        
        # 获取动作信息
        print(action.to_string())  # 打印 "↑" 或 "↘"
        print(action.direction())  # 打印 Position(-1, 0) 或 Position(1, 1)
    """
    # __slots__ 限制此类只能有index_v一个属性, 减少内存占用
    __slots__ = ('index_v',)

    def __init__(self, action_idx: int = 0):
        """
        @brief 构造函数
        
        @param action_idx: 动作索引 [0, 8]
        - 0: 上 (↑)
        - 1: 右上 (↗)
        - 2: 右 (→)
        - 3: 右下 (↘)
        - 4: 下 (↓)
        - 5: 左下 (↙)
        - 6: 左 (←)
        - 7: 左上 (↖)
        - 8: 原地不动 (□)
        
        @note 如果传入无效索引(>=9), 自动设置为8(原地不动)
        """
        # 边界检查: 确保索引在有效范围内 [0, 8]
        # 如果索引 >= 9, 默认为原地不动
        self.index_v: int = action_idx if action_idx < K_ACTION_COUNT else 8

    @staticmethod
    def random() -> 'Action':
        """
        @brief 创建随机动作
        
        @return 随机选择的Action实例
        
        @note 用于 epsilon-greedy 探索策略
        @note 9个动作等概率随机选择
        
        @example
            action = Action.random()  # 随机选择一个动作
        """
        import random
        # randint是闭区间, 所以范围是 [0, 8]
        return Action(random.randint(0, K_ACTION_COUNT - 1))

    @staticmethod
    def from_index(idx: int) -> 'Action':
        """
        @brief 从索引创建动作
        
        @param idx: 动作索引 [0, 8]
        @return Action实例
        
        @note 这是构造函数的别名, 提供更语义化的工厂方法
        @note 等同于 Action(idx)
        
        @example
            action = Action.from_index(4)  # 创建向下动作
        """
        return Action(idx)

    def index(self) -> int:
        """
        @brief 获取动作索引
        
        @return 动作索引 [0, 8]
        
        @example
            action = Action(3)
            idx = action.index()  # 返回 3
        """
        return self.index_v

    def to_string(self) -> str:
        """
        @brief 获取动作的Unicode字符表示
        
        @return 动作字符, 如 "↑", "↗", "□" 等
        
        @note 用于可视化显示, 让训练输出更易读
        
        @example
            action = Action(0)
            print(action.to_string())  # 输出: ↑
        """
        # K_ACTION_CHARS = "↑↗→↘↓↙←↖□"
        # 索引0返回'↑', 索引8返回'□'
        return K_ACTION_CHARS[self.index_v]

    def direction(self) -> Position:
        """
        @brief 获取动作对应的方向向量
        
        @return Position对象, 表示(row_offset, col_offset)
        
        @note 这个向量表示执行这个动作后, 位置的(row, col)变化量
        
        @example
            action = Action(0)  # UP
            pos = action.direction()  # Position(-1, 0)
            # 如果智能体在(10, 10), 执行动作后移动到(9, 10)
            
            action = Action(3)  # RIGHT-DOWN
            pos = action.direction()  # Position(1, 1)
            # 如果智能体在(10, 10), 执行动作后移动到(11, 11)
        """
        # K_DIRECTION_ROW 和 K_DIRECTION_COL 是平行数组
        # 通过索引获取对应动作的行/列偏移量
        # 例如索引0: row=-1, col=0 (向上移动)
        return Position(K_DIRECTION_ROW[self.index_v], K_DIRECTION_COL[self.index_v])
