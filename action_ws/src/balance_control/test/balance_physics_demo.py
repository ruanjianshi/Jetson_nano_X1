#!/usr/bin/env python3
"""
轮腿机器人平衡物理演示
=======================

物理模型:
  轮腿机器人直立时可简化为倒立摆 (Inverted Pendulum on Wheels)

  ┌─── 机体 (质量 M, 转动惯量 I)
  │  θ ← 倾倒角 (pitch)
  │
  ├─── 腿连杆 (可调整几何)
  │
  └─── 轮子 (半径 r, 转动惯量 J)
       └── 地面接触点

失衡检测:
  当 |pitch| > threshold (如 0.02 rad ≈ 1.15°) 或 |ω_y| 持续增长时,判定失衡

恢复力来源:
  1. 轮子加速度 → 地面反力 → 恢复力矩 (主控制)
     轮转矩 τ_wheel → 地面反力 F = τ_wheel / r
     恢复力矩 M = F × h = (τ_wheel / r) × h·cos(θ)
     
  2. 腿几何变化 → 质心偏移 → 重力矩变化 (辅控制)
     髋伸展 → 轮后移 → 地面支撑点后移 → 质心前移被抵消

状态方程 (线性化, 小角度 θ):
  (I + M·h²)·θ̈ = M·g·h·θ + τ_wheel
                   ↑重力矩    ↑轮子反力矩
  
  PD控制器: τ_wheel = -Kp·θ - Kd·θ̇
  闭环: (I+Mh²)·θ̈ + Kd·θ̇ + (Kp - Mgh)·θ = 0
  
  稳定条件: Kp > Mgh (约 12.59 × 9.81 × 0.35 ≈ 43.2 Nm/rad)

输入: roll pitch yaw [rad] + 可选角速度
输出: 各算法计算出的轮速/力矩 + 腿关节力矩

用法:
  python3 balance_physics_demo.py 0 0.15 0     # 前倾15°
  python3 balance_physics_demo.py -i            # 交互模式
"""

import math
import sys

# URDF提取的机器人参数
M = 12.59          # 总质量 [kg]
g = 9.81           # 重力 [m/s²]
h = 0.35           # 质心高度 [m]
wheel_radius = 0.10  # 轮半径 [m]
wheel_base = 0.40   # 轮距 [m]

# 转动惯量估算 (简化: 细杆 I=1/3*M*h²)
I_body = 1.0 / 3.0 * M * h * h   # ≈ 0.51 kg·m²

# PID增益
Kp = 80.0    # 比例 [Nm/rad], 需 > Mgh ≈ 43.2
Kd = 10.0    # 微分 [Nm·s/rad]
Ki = 1.0     # 积分 (可选)

def wheel_pd_balance(pitch, pitch_dot, dt=0.002):
    """
    基于轮子驱动的倒立摆PD平衡控制器
    
    返回: (left_wheel_torque, right_wheel_torque, stability_margin)
    
    前倾 (pitch>0):   轮子需正力矩 (加速前行),产生反作用力矩推回机体
    后仰 (pitch<0):   轮子需负力矩 (减速/后退)
    """
    global _integral
    _integral += pitch * dt
    
    # PD控制
    tau = -(Kp * pitch + Kd * pitch_dot + Ki * _integral)
    
    # 每轮平分 (可叠加差速控制yaw)
    tau_L = tau / 2.0
    tau_R = tau / 2.0
    
    # 稳定性裕度: 有效刚度 / 临界刚度
    effective_stiffness = Kp / (M * g * h)
    stability_margin = effective_stiffness - 1.0  # >0表示稳定
    
    return tau_L, tau_R, stability_margin

_integral = 0.0

def wheel_velocity_from_torque(tau, dt):
    """力矩→轮角速度 (简化刚体模型)"""
    J_wheel = 2.323 * wheel_radius * wheel_radius / 2.0  # 轮转动惯量
    alpha = tau / max(J_wheel, 1e-6)
    return alpha * dt

def check_balance_state(pitch, pitch_dot, body_height=0.35):
    """
    判断机器人平衡状态
    
    返回: (状态, 描述, 严重程度)
    
    状态定义:
      OK         |θ|<0.02 且 |θ̇|<0.1 → 稳定平衡
      DRIFTING   |θ|<0.05 且 |θ̇|<0.3 → 微小漂移,可自动恢复
      TILTING    |θ|<0.30 且 |θ̇|<1.5 → 明显倾斜,需主动修正
      FALLING    |θ|≥0.30 或 |θ̇|≥1.5 → 即将倾倒,需紧急干预
    """
    abs_p = abs(pitch)
    abs_pd = abs(pitch_dot)
    
    if abs_p >= 0.30 or abs_pd >= 1.5:
        return "FALLING", "即将倾倒! 倾角=%.1f° ω=%.1f rad/s" % (math.degrees(pitch), pitch_dot), 3
    elif abs_p >= 0.05 or abs_pd >= 0.3:
        return "TILTING", "明显倾斜 倾角=%.1f° ω=%.1f rad/s" % (math.degrees(pitch), pitch_dot), 2
    elif abs_p >= 0.02 or abs_pd >= 0.1:
        return "DRIFTING", "微小漂移 倾角=%.1f° ω=%.1f rad/s" % (math.degrees(pitch), pitch_dot), 1
    else:
        return "OK", "稳定平衡 倾角=%.1f°" % (math.degrees(pitch)), 0

def simulate_recovery(pitch_init, pitch_dot_init=0, dt=0.002, max_steps=5000):
    """
    模拟平衡恢复过程
    
    欧拉积分:
      θ̈ = (Mgh·θ + τ_wheel) / (I_body + Mh²)
      θ̇ += θ̈·dt
      θ += θ̇·dt
    
    返回: [(t, pitch, pitch_dot, tau_L, tau_R, state), ...]
    """
    global _integral
    _integral = 0.0
    
    pitch = pitch_init
    pitch_dot = pitch_dot_init
    
    I_total = I_body + M * h * h  # 总转动惯量
    
    history = []
    
    for step in range(max_steps):
        tau_L, tau_R, margin = wheel_pd_balance(pitch, pitch_dot, dt)
        tau_total = tau_L + tau_R
        
        # 动力学: θ̈ = (重力矩 + 控制力矩) / 总惯量
        gravity_torque = M * g * h * math.sin(pitch)
        pitch_accel = (gravity_torque + tau_total) / I_total
        
        # 欧拉积分
        pitch_dot += pitch_accel * dt
        pitch += pitch_dot * dt
        
        state, desc, severity = check_balance_state(pitch, pitch_dot)
        
        if step % 100 == 0:
            history.append((step * dt, pitch, pitch_dot, tau_L, tau_R, state))
        
        # 收敛判断
        if abs(pitch) < 0.001 and abs(pitch_dot) < 0.001:
            history.append((step * dt, pitch, pitch_dot, tau_L, tau_R, "OK"))
            break
    else:
        # 超过最大步数仍不收敛
        history.append((max_steps * dt, pitch, pitch_dot, tau_L, tau_R, "DIVERGED"))
    
    return history

def print_physics_explanation():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           轮腿机器人 平衡恢复 物理原理                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ┌─ 失衡检测 ──────────────────────────────────────────┐     ║
║  │                                                      │     ║
║  │  正常: |pitch| < 0.02 rad (≈1.1°)                    │     ║
║  │  预警: |pitch| > 0.05 rad (≈2.9°)                    │     ║
║  │  紧急: |pitch| > 0.30 rad (≈17°)                     │     ║
║  │                                                      │     ║
║  │  角速度加速增大 → 即将倾倒 → 触发应急保护            │     ║
║  └──────────────────────────────────────────────────────┘     ║
║                                                              ║
║  ┌─ 轮子平衡 (主要机制, 类Segway) ───────────────────┐       ║
║  │                                                      │     ║
║  │  前倾(+θ): 重力矩 Mgh·sin(θ) 加速倾倒              │     ║
║  │           轮子向前加速 → 地面反力向后              │     ║
║  │           反力×杆长 → 对机体产生向后恢复力矩        │     ║
║  │                                                      │     ║
║  │  τ = -(Kp·θ + Kd·θ̇)                                  │     ║
║  │                                                      │     ║
║  │  前倾(+0.15rad) → τ > 0 → 轮子正转加速              │     ║
║  │  后仰(-0.15rad) → τ < 0 → 轮子反转(后退)           │     ║
║  │  稳定条件: Kp > Mgh ≈ 43.2 Nm/rad                  │     ║
║  └──────────────────────────────────────────────────────┘     ║
║                                                              ║
║  ┌─ 腿关节辅助 (COM调节) ───────────────────────────┐       ║
║  │                                                      │     ║
║  │  髋伸展: 轮后移 → 支撑面后移 → 质心回到支撑面上    │     ║
║  │  膝弯曲: 降低质心 → 减小重力矩 → 降低晃动频率      │     ║
║  │                                                      │     ║
║  │  作用于 pitch 的 hip_pitch + knee_pitch             │     ║
║  │  作用于 roll  的 hip_roll                           │     ║
║  └──────────────────────────────────────────────────────┘     ║
║                                                              ║
║  ┌─ 差速轮 yaw 控制 ─────────────────────────────────┐      ║
║  │                                                      │     ║
║  │  left_wheel > right_wheel → 右转                     │     ║
║  │  两轮同向加速/减速不影响yaw                         │     ║
║  │  yaw角: 对轮速差积分                                 │     ║
║  └──────────────────────────────────────────────────────┘     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

def main():
    print_physics_explanation()
    
    if len(sys.argv) >= 2 and sys.argv[1] == '-i':
        # 交互模式
        print("进入交互模式 (输入 roll pitch yaw 或 q 退出)")
        while True:
            try:
                line = input("\n> ").strip()
                if not line or line == 'q':
                    break
                parts = line.split()
                roll, pitch, yaw = float(parts[0]), float(parts[1]), float(parts[2])
                pd = float(parts[3]) if len(parts) > 3 else 0.0
                run_one(pitch, pd)
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"Error: {e}")
    elif len(sys.argv) >= 3:
        pitch = float(sys.argv[1])
        pitch_dot = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        run_one(pitch, pitch_dot)
    else:
        # 默认演示: 前倾15°
        print("默认演示: 前倾 0.15 rad (8.6°), 静止初始")
        run_one(0.15, 0.0)

def run_one(pitch, pitch_dot):
    state, desc, severity = check_balance_state(pitch, pitch_dot)
    
    # 重力矩
    gravity_torque = M * g * h * math.sin(pitch)
    
    # PD输出
    global _integral
    _integral = 0.0
    tau_L, tau_R, margin = wheel_pd_balance(pitch, pitch_dot)
    tau_total = tau_L + tau_R
    
    # 轮速
    v_L = wheel_velocity_from_torque(tau_L, 0.002)
    v_R = wheel_velocity_from_torque(tau_R, 0.002)
    
    print(f"""
┌──────────────────────────────────────────────┐
│  失衡判断: {state:8s}                        │
│  描述:     {desc}                             │
│  严重程度: {'●●●'[:severity]}{'○○○'[severity:]}                            │
├──────────────────────────────────────────────┤
│  倾角:     {pitch:+.3f} rad ({math.degrees(pitch):+6.1f}°)              │
│  角速度:   {pitch_dot:+.3f} rad/s                     │
├──────────────────────────────────────────────┤
│  重力矩:   {gravity_torque:+.2f} Nm                     │
│  控制力矩: {tau_total:+.2f} Nm                     │
│   左轮力:  {tau_L:+.2f} Nm                     │
│   右轮力:  {tau_R:+.2f} Nm                     │
│  稳定裕度: {margin:+.2f} (>0=稳定)               │
├──────────────────────────────────────────────┤
│  左轮速:   {v_L:+.3f} rad/s                     │
│  右轮速:   {v_R:+.3f} rad/s                     │
│  左轮速:   {v_L*wheel_radius:+.3f} m/s                      │
│  右轮速:   {v_R*wheel_radius:+.3f} m/s                      │
├──────────────────────────────────────────────┤
│  腿关节:                                      │
│  hip_pitch: {-(Kp*pitch+Kd*pitch_dot)*0.5:+.2f} Nm (辅助COM偏移)          │
│  knee:      {-(Kp*pitch+Kd*pitch_dot)*0.25:+.2f} Nm                     │
│  hip_roll:  0.00 Nm (无侧倾)                  │
└──────────────────────────────────────────────┘""")
    
    # 模拟恢复过程
    print("\n  ┌─ 恢复过程模拟 (dt=2ms) ─────────────────────┐")
    print("  │ 时刻(s)  pitch(°)  ω(rad/s)  τ_wheel 状态  │")
    print("  ├────────────────────────────────────────────┤")
    
    history = simulate_recovery(pitch, pitch_dot)
    
    for t, p, pd, tl, tr, st in history:
        print(f"  │ {t:6.3f}   {math.degrees(p):+7.2f}  {pd:+8.3f}  {tl+tr:+7.1f}  {st:8s} │")
    
    final_p, final_pd = history[-1][1], history[-1][2]
    final_state = history[-1][5]
    
    print("  └────────────────────────────────────────────┘")
    
    if final_state == "OK":
        print(f"\n  ✅ 恢复成功!  耗时 {history[-1][0]:.2f}s  残留倾角 {math.degrees(final_p):.3f}°")
    elif final_state == "DIVERGED":
        print(f"\n  ⚠️  不收敛! 增益Kp={Kp} 可能不足 (需 > {M*g*h:.1f})")

if __name__ == '__main__':
    main()
