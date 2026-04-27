# C++ 代码设计与工程开发规范（优化版）

> **版本**: v3.0.0
> **更新日期**: 2026-04-16
> **适用项目**: `code_design_sample`
> **C++ 标准**: `C++17`
> **日志库**: `spdlog`
> **构建系统**: `CMake`

---

## 1. 文档定位

### 1.1 目标

本规范用于统一项目的：

- 代码命名与布局
- 接口设计与模块边界
- 错误处理与资源管理
- 测试、静态检查与 CI 门禁
- 代码评审与交付标准

目标是让代码具备：

- 一致性
- 可读性
- 可维护性
- 可测试性
- 可演进性
- 可管理性

### 1.2 规范等级

本文规则按以下等级执行：

- `MUST`：必须遵守，违反需在 PR 中说明原因
- `SHOULD`：默认遵守，确有收益时可例外
- `MAY`：可选项，按场景采用

### 1.3 适用范围

本规范适用于：

- `include/`
- `src/`
- `tests/`
- `log/`
- `tools/`

以下内容默认不强制适用：

- 第三方库代码
- 自动生成代码
- 外部镜像代码

---

## 2. 开发原则

### 2.1 简单优先

- `MUST` 优先最小可行实现
- `MUST` 不为一次性需求引入额外抽象
- `MUST` 不为假想场景过度设计
- `SHOULD` 当 50 行能解决时，不写成 200 行

### 2.2 接口显式

- `MUST` 公共接口明确输入、输出、所有权、错误语义
- `MUST` 公共接口明确线程安全语义
- `MUST` 不隐藏重要前置条件
- `SHOULD` 优先让接口自解释，而不是依赖阅读实现

### 2.3 默认安全

- `MUST` 资源通过 RAII 管理
- `MUST` 所有权必须清晰
- `MUST` 边界条件必须显式处理
- `MUST` 禁止未定义行为依赖

### 2.4 可测试优先

- `MUST` 模块设计可做单元测试
- `MUST` 外设、时间、文件、网络等依赖可替换或可注入
- `SHOULD` Bug 修复先补复现测试，再修复

### 2.5 精准修改

- `MUST` 只修改与当前需求直接相关的代码
- `MUST` 不顺手重构无关模块
- `MUST` 不在同一 PR 中混入风格整理和逻辑变更
- `SHOULD` 清理本次改动引入的未使用代码

---

## 3. 命名规范

### 3.1 总体规则

| 类别 | 规则 | 示例 |
|---|---|---|
| 文件/目录 | 小写 + 下划线 | `temperature_sensor.h` |
| 命名空间 | 小写 + 下划线 | `code_project::sensor_driver` |
| 宏 | 全大写 + 下划线 | `MAX_BUFFER_SIZE` |
| 常量 | `constexpr` 优先，名字小写下划线 | `max_buffer_size` |
| 类型别名 | 小写 + 下划线 + `_t` | `sensor_id_t` |
| 接口类 | 小写 + 下划线 + `_base_t` | `sensor_base_t` |
| 实现类 | 小写 + 下划线 + `_impl_t` | `sensor_impl_t` |
| 私有实现类 | 小写 + 下划线 + `_priv_t` | `sensor_priv_t` |
| 位域结构体 | 小写 + 下划线 + `_bits_t` | `status_bits_t` |
| 联合体 | 小写 + 下划线 + `_u` | `status_u` |
| 回调类型 | 小写 + 下划线 + `_cb_t` | `data_ready_cb_t` |
| 函数 | 小写 + 下划线 | `read_once()` |

### 3.2 关于 `_t` 的约束

- `MUST` 项目自定义 `_t` 类型放在项目命名空间内
- `MUST NOT` 在全局命名空间新增项目私有 `_t` 类型
- `SHOULD` 新代码优先 `using`，不优先 `typedef`

### 3.3 变量命名

| 类型 | 推荐规则 | 示例 |
|---|---|---|
| 普通变量 | 语义化命名，可保留 `_v` | `temperature_v` |
| 指针 | 非拥有指针可用 `_p` | `buffer_p` |
| 数组 | `_m` | `raw_data_m` |
| 成员变量 | 语义化 + 可选后缀 | `is_initialized_v` |
| 回调成员 | `_cb_p` 或语义化命名 | `data_ready_cb_p` |

### 3.4 变量命名原则

- `MUST` 变量名表达业务含义
- `SHOULD` 底层驱动、寄存器映射、协议解析模块保留 `_v/_p/_m` 风格
- `SHOULD` 业务逻辑层优先语义命名，避免后缀泛滥
- `MUST NOT` 使用 `tmp1`、`data2`、`flag` 这类弱语义名字，除非作用域极小

---

## 4. 类型与常量规范

### 4.1 基本规则

- `MUST` 使用固定宽度整数类型，如 `std::uint32_t`
- `MUST` 布尔状态使用 `bool`
- `MUST` 常量优先 `constexpr`
- `MUST NOT` 用宏替代普通常量
- `SHOULD` 用 `std::array` 代替固定大小 C 数组，除非有 ABI/HAL 限制

### 4.2 枚举规范

- `MUST` C++ 接口优先使用 `enum class`
- `MUST` 指定底层类型，特别是在协议、寄存器、序列化场景
- `SHOULD` 仅 C 兼容头文件使用 `typedef enum`

```cpp
enum class sensor_state_t : std::uint8_t {
    IDLE = 0,
    MEASURING,
    WAITING,
    ERROR_STATE
};
```

### 4.3 结构体规范

- `MUST` 纯数据对象优先使用 `struct`
- `MUST` 字段单位明确
- `MUST` 传感器、协议、硬件配置结构体写清默认值和范围
- `SHOULD` 输出参数超过一个时，优先返回结构体而不是多个裸指针

---

## 5. 接口设计规范

### 5.1 公共接口要求

每个公共接口都必须明确：

- 功能语义
- 参数含义与单位
- 返回值与错误码
- 前置条件
- 后置条件
- 线程安全约束
- 所有权约束

### 5.2 接口设计原则

- `MUST` 多实现替换需求明确时，才引入抽象基类
- `MUST` 使用 `override`
- `SHOULD` 对不希望被继承的类使用 `final`
- `MUST` 构造函数只做轻量初始化
- `SHOULD` 可能失败的重操作放到 `initialize()`
- `MUST NOT` 让调用者猜测对象是否可重复初始化、是否可重复停止

### 5.3 C++ 接口与 C 接口分离

- `MUST` C++ 原生接口放在 `.h/.cpp` 中，使用命名空间、类、RAII
- `MUST` 若提供 C 兼容接口，单独放在 `xxx_c.h/xxx_c.cpp`
- `MUST NOT` 在同一个头文件中混合完整 C++ 面向对象接口和 C 句柄式接口模板

---

## 6. 类设计与 Pimpl

### 6.1 何时使用 Pimpl

仅在以下场景使用 Pimpl：

- 需要稳定 ABI
- 需要隔离重依赖头文件
- 实现细节变化频繁，编译成本高
- 需要隐藏平台实现细节

### 6.2 何时不要使用 Pimpl

- 小型值类型
- 仅有少量成员、逻辑简单的类
- 生命周期和依赖都很简单的工具类

### 6.3 Pimpl 规则

- `MUST` 明确拷贝/移动策略
- `MUST` 使用 `std::unique_ptr`
- `MUST` 析构函数在 `.cpp` 中定义
- `SHOULD` 默认禁用拷贝，只在语义明确时实现深拷贝
- `MUST NOT` 机械套用 `base + impl + factory + pimpl`

```cpp
class sensor_impl_t final : public sensor_base_t {
public:
    sensor_impl_t();
    ~sensor_impl_t() override;

    sensor_impl_t(const sensor_impl_t&) = delete;
    sensor_impl_t& operator=(const sensor_impl_t&) = delete;
    sensor_impl_t(sensor_impl_t&&) noexcept = default;
    sensor_impl_t& operator=(sensor_impl_t&&) noexcept = default;

private:
    class sensor_priv_t;
    std::unique_ptr<sensor_priv_t> p_impl_p;
};
```

---

## 7. 错误处理规范

### 7.1 总原则

- `MUST` 项目统一错误处理策略
- `MUST` 驱动层、基础库边界禁止异常跨边界传播
- `MUST` 公共接口统一返回错误码或明确的结果对象
- `MUST` 日志不能替代错误返回
- `MUST NOT` 静默吞掉错误

### 7.2 推荐策略

- 驱动/HAL/协议层：返回 `xxx_err_t`
- 业务组合层：可封装为更高层结果对象
- 构造阶段：仅做不失败或极少失败的操作
- 初始化阶段：处理可能失败的外设、IO、句柄绑定

### 7.3 错误码规范

- `MUST` 错误码可枚举、可比较、可记录
- `MUST` 区分参数错误、状态错误、外部依赖错误、超时错误、校验错误
- `SHOULD` 同一模块错误码语义一致

```cpp
enum class sensor_err_t : std::int32_t {
    OK = 0,
    NULL_PTR = -1,
    NOT_INITIALIZED = -2,
    I2C_FAILED = -3,
    CRC_FAILED = -4,
    TIMEOUT = -5
};
```

---

## 8. 资源管理与生命周期

### 8.1 所有权规则

- `MUST` 裸指针默认表示非拥有关系
- `MUST` 资源用对象生命周期管理
- `MUST` 禁止随意出现裸 `new/delete`
- `SHOULD` 独占资源使用 `std::unique_ptr`
- `SHOULD` 共享资源仅在确有共享所有权时使用 `std::shared_ptr`

### 8.2 RAII 规则

- `MUST` 文件、锁、线程、句柄、socket、缓冲区等资源使用 RAII
- `MUST` 失败路径不泄漏资源
- `MUST` 析构函数不抛异常
- `SHOULD` 移动构造和移动赋值标记 `noexcept`

---

## 9. 并发与线程安全

### 9.1 线程安全声明

每个公共类必须明确属于以下哪一种：

- 线程不安全
- 只读线程安全
- 外部同步
- 内部同步

### 9.2 并发规则

- `MUST` 共享可变状态受同步保护
- `MUST` 锁顺序固定，避免死锁
- `MUST NOT` 在持锁状态下调用外部回调
- `MUST NOT` 在回调中做长时间阻塞
- `SHOULD` 原子变量仅用于简单状态，不替代完整同步设计

### 9.3 状态机规则

- `MUST` 非阻塞状态机的状态转移可读、可测试
- `MUST` 明确超时、错误恢复、重复调用行为
- `SHOULD` 状态转移使用单一入口，避免分散写状态

---

## 10. 模块化与目录规范

### 10.1 目录结构

```text
project/
├── include/
│   ├── code_project/         # 嵌入式/驱动项目示例
│   │   ├── core/
│   │   ├── driver/
│   │   ├── protocol/
│   │   └── utils/
│   └── rl_project/          # 强化学习项目示例
│       ├── core/
│       ├── env/
│       ├── agent/
│       └── utils/
├── src/
│   ├── code_project/
│   │   ├── core/
│   │   ├── driver/
│   │   ├── example/
│   │   ├── protocol/
│   │   └── utils/
│   └── rl_project/
│       ├── core/
│       ├── env/
│       ├── agent/
│       ├── example/
│       └── utils/
├── tests/
│   ├── code_project/
│   │   ├── core/
│   │   ├── driver/
│   │   └── protocol/
│   └── rl_project/
│       ├── core/
│       ├── env/
│       └── agent/
├── log/
│   ├── code_project/
│   │   ├── core/
│   │   ├── driver/
│   │   ├── protocol/
│   │   └── utils/
│   └── rl_project/
│       ├── core/
│       ├── env/
│       ├── agent/
│       └── utils/
├── cmake/
└── docs/
```

### 10.2 模块边界

- `MUST` 一个模块只负责一个核心职责
- `MUST` 上层依赖下层，下层不得反向依赖上层
- `MUST` `include/` 只放公开头文件
- `MUST NOT` 跨模块包含 `src/` 内部头
- `SHOULD` 内部实现放 `detail/` 或 `internal/`

### 10.3 文件组织

- `MUST` `.h` 与 `.cpp` 成对出现
- `SHOULD` 每个模块有独立测试文件
- `SHOULD` 大文件按区块组织：类型、常量、私有函数、生命周期、核心逻辑、辅助函数

---

## 11. 日志、断言与配置

### 11.1 日志规范

- `MUST` 统一使用 `spdlog`
- `MUST` 错误日志包含上下文信息
- `MUST NOT` 在热路径打印高频无价值日志
- `SHOULD` 日志级别统一：`trace/debug/info/warn/error/critical`

### 11.2 断言规范

- `MUST` `assert` 用于程序员错误和不变量检查
- `MUST NOT` 用 `assert` 处理用户输入或运行期外部错误
- `SHOULD` 运行期可恢复错误走正常错误处理链路

### 11.3 配置规范

- `MUST` 配置项集中定义
- `MUST` 配置值给出单位、范围、默认值
- `SHOULD` 避免散落的魔法数

---

## 12. 注释与文档规范

### 12.1 注释原则

- `MUST` 注释解释"为什么"，而不是重复"代码做了什么"
- `MUST` 公共 API 写 Doxygen 注释
- `MUST` 硬件时序、协议字段、兼容性绕过必须注释
- `MUST NOT` 写无意义注释

### 12.2 Doxygen 注释规范

**文件级注释**：
```cpp
/**
 * @file  filename.h
 * @brief 简要功能说明
 * @note  补充说明（可选）
 */
```

**类/结构体注释**：
```cpp
/**
 * @brief  类功能简要说明
 * @details 详细说明（可选）
 */
class my_class_t {
```

**枚举值注释**：
```cpp
enum class sensor_state_t : std::uint8_t {
    IDLE = 0,           ///< 空闲状态
    RUNNING,            ///< 运行中
    ERROR_STATE         ///< 错误状态
};
```

**函数注释**：
```cpp
/**
 * @brief       函数功能简要说明
 * @param[in]   param_name 参数说明
 * @param[out]  output_param 输出参数说明
 * @return      返回值说明
 * @retval      OK 成功
 * @retval      NULL_PTR 空指针错误
 * @note        线程安全性、前置条件等
 */
core::status_t initialize();
```

**命名空间注释**：
```cpp
namespace code_project::driver {  // NOLINT
```

### 12.3 设计文档

- `SHOULD` 重大架构变更编写 ADR
- `SHOULD` 公共模块维护使用说明和边界约束
- `SHOULD` 破坏性修改记录在 `CHANGELOG`

---

## 13. 测试与质量门禁

### 13.1 测试要求

- `MUST` 每个公共模块具备单元测试
- `MUST` 每个 Bug 修复至少附带一个回归测试
- `MUST` 覆盖正常路径、边界路径、错误路径
- `SHOULD` 驱动层通过 mock 或 fake 替代真实硬件
- `SHOULD` 核心算法与状态机单独测试

### 13.2 编译与静态检查

- `MUST` 开启高等级警告
- `MUST` CI 中警告视为错误
- `MUST` 接入 `clang-format`
- `MUST` 接入 `clang-tidy`
- `SHOULD` Debug/CI 开启 `AddressSanitizer` 和 `UndefinedBehaviorSanitizer`

### 13.3 推荐编译选项

```cmake
target_compile_features(code_project PUBLIC cxx_std_17)

target_compile_options(code_project PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wsign-conversion
)
```

### 13.4 CI 门禁

PR 合并前必须通过：

- 编译成功
- 单元测试通过
- 格式检查通过
- 静态检查通过
- 必要的 Sanitizer 检查通过

---

## 14. Code Review 规范

每次评审至少检查以下内容：

- 接口语义是否清晰
- 所有权是否明确
- 错误处理是否统一
- 是否引入无意义抽象
- 是否易于测试
- 是否破坏模块边界
- 是否存在线程安全风险
- 是否引入兼容性问题
- 注释和文档是否同步更新

---

## 15. Definition of Done

任务完成必须满足：

- 需求实现完成
- 测试通过
- 无新增编译警告
- 无新增静态检查高优先级问题
- 文档和注释已更新
- 变更可被 reviewer 理解和维护
- 无明显未清理的临时代码

---

## 16. 示例代码参考

参考 `include/code_project/driver/` 下的传感器驱动示例：

- `sensor_base.h` - 抽象接口 (`_base_t`)
- `sensor_impl.h` - Pimpl 实现 (`_impl_t`)
- `sensor_types.h` - 类型定义 (`_t` 后缀)
- `sensor_c.h` - C 兼容接口

---

## 17. 配套文件

本规范配合以下文件使用：

- `.clang-format` - 代码格式化配置
- `.clang-tidy` - 静态检查配置
- `docs/adr/` - 架构决策记录 (ADR)
- `CONTRIBUTING.md` - 贡献指南
- `CHANGELOG.md` - 变更日志

---

## 参考资料

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/)
- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide)
- [LLVM Coding Standards](https://llvm.org/docs/CodingStandards.html)
- [SEI CERT C++ Coding Standard](https://www.sei.cmu.edu/library/sei-cert-c-and-c-coding-standards/)
