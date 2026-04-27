# 日志规范 (LOGGING_STANDARDS)

> **版本**: v1.0.0
> **更新日期**: 2026-04-27
> **适用项目**: `code_design_sample`
> **日志库**: `spdlog`

---

## 1. 文档定位

本规范定义项目日志的：
- 目录结构与文件组织
- 命名约定
- 级别定义与使用场景
- 格式规范
- 管理策略

目标是使日志具备：
- 可读性：格式统一，信息清晰
- 可追溯性：便于问题定位
- 可管理性：控制存储成本
- 可配置性：支持不同场景

---

## 2. 目录结构

### 2.1 目录组织

```
log/
└── code_project/
    ├── core/          # 核心模块日志
    ├── driver/        # 驱动模块日志
    ├── protocol/      # 协议模块日志
    └── utils/         # 工具模块日志
```

**规则**：
- `MUST` 日志目录结构与 `src/code_project/` 保持一致
- `MUST` 各模块日志写入对应子目录
- `SHOULD` 日志按模块分离，便于定位问题

### 2.2 日志文件命名

```
{module}_{type}_{date}.log
```

示例：
- `sensor_info_2026-04-27.log` - 传感器驱动 info 级别日志
- `protocol_error_2026-04-27.log` - 协议模块 error 级别日志
- `core_debug_2026-04-27.log` - 核心模块 debug 级别日志

**规则**：
- `MUST` 使用小写 + 下划线命名
- `MUST` 包含日期后缀，格式 `YYYY-MM-DD`
- `SHOULD` 按级别分离：`_info`, `_warn`, `_error`, `_debug`

---

## 3. 日志级别

### 3.1 级别定义

| 级别 | 用途 | 示例场景 |
|------|------|----------|
| `trace` | 最详细调试信息 | 函数入口/出口、循环变量 |
| `debug` | 开发调试信息 | 中间状态、算法步骤 |
| `info` | 正常运行信息 | 初始化完成、数据收发 |
| `warn` | 异常但可恢复 | 超时重试、边界值 |
| `error` | 错误但可处理 | IO 失败、重试耗尽 |
| `critical` | 严重错误需退出 | 致命初始化失败 |

### 3.2 使用规则

- `MUST` 生产环境默认级别 `info`
- `MUST` 热路径禁止 `trace/debug` 日志
- `MUST` 错误日志必须包含上下文（模块名、函数名、错误码）
- `SHOULD` 循环中的日志使用条件判断，避免高频输出

```cpp
// ✅ 正确：循环中按条件打印
for (int i = 0; i < 10; ++i) {
    if (i % 1000 == 0) {
        SPDLOG_DEBUG("processing index: {}", i);
    }
}

// ❌ 错误：热路径高频日志
for (int i = 0; i < 100000; ++i) {
    SPDLOG_TRACE("index: {}", i);  // 禁止
}
```

---

## 4. 日志格式

### 4.1 格式规范

```
[{timestamp}] [{level}] [{module}] [{thread_id}] {message}
```

示例：
```
[2026-04-27 10:30:15.123] [INFO] [driver/sensor] [0x7f2a] sensor init success
[2026-04-27 10:30:16.456] [WARN] [driver/sensor] [0x7f2a] i2c timeout, retry 1/3
[2026-04-27 10:30:17.789] [ERROR] [driver/sensor] [0x7f2a] i2c failed after 3 retries
```

### 4.2 字段说明

| 字段 | 格式 | 说明 |
|------|------|------|
| timestamp | `YYYY-MM-DD HH:MM:SS.mmm` | 毫秒精度 |
| level | `TRACE/DEBUG/INFO/WARN/ERROR/CRITICAL` | 大写 |
| module | `category/subcategory` | 如 `driver/sensor` |
| thread_id | 十六进制 | 可选，生产环境建议关闭 |
| message | 自定义 | 包含关键数据 |

### 4.3 上下文信息

错误日志必须包含：
- 模块/类名
- 函数名
- 错误码或错误描述
- 相关参数值

```cpp
SPDLOG_ERROR("[driver/sensor] {} failed, err={}, param={}",
             __func__, static_cast<int>(err), param_v);
```

---

## 5. spdlog 配置

### 5.1 基础配置

```cpp
#include <spdlog/sinks/rotating_file_sink.h>
#include <spdlog/sinks/stdout_color_sinks.h>

auto logger = spdlog::rotating_logger_mt(
    "sensor_logger",
    "log/code_project/driver/sensor_info_2026-04-27.log",
    1024 * 1024 * 10,  // 10MB per file
    5                   // 5 files max
);
logger->set_level(spdlog::level::info);
logger->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] [%t] %v");
```

### 5.2 多级别日志器

```cpp
// 按级别分离 sink
auto info_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
    "log/code_project/driver/sensor_info.log", 10*1024*1024, 3);
auto error_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
    "log/code_project/driver/sensor_error.log", 10*1024*1024, 3);

// 组合 logger
spdlog::logger logger("sensor", {info_sink, error_sink});
logger.set_level(spdlog::level::debug);
```

### 5.3 异步日志

```cpp
spdlog::init_thread_pool(8192, 1);
auto file_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
    "log/code_project/driver/sensor.log", 10*1024*1024, 3);
spdlog::logger logger("sensor",
    std::make_shared<spdlog::sinks::dist_sink_st>>(file_sink));
```

---

## 6. 日志管理策略

### 6.1 日志轮转

- `MUST` 单文件大小上限 10MB
- `MUST` 保留文件数量不超过 5 个
- `SHOULD` 按日期轮转，保留 7 天

### 6.2 日志清理

```bash
# 清理 7 天前日志
find log -name "*.log" -mtime +7 -delete
```

### 6.3 磁盘监控

- `SHOULD` 监控日志目录磁盘使用
- `SHOULD` 磁盘使用超过 80% 时告警

---

## 7. 模块日志职责

### 7.1 core 模块
- 初始化/销毁日志
- 状态转换日志
- 资源分配/释放日志

### 7.2 driver 模块
- 硬件初始化成功/失败
- 通信超时、重试
- 配置变更

### 7.3 protocol 模块
- 协议解析开始/完成
- 校验失败、字段异常
- 报文收发（debug 级别）

### 7.4 utils 模块
- 工具函数入口/出口
- 性能数据（可选）

---

## 8. 最佳实践

### 8.1 日志要点

- ✅ 使用结构化日志，便于解析
- ✅ 错误日志包含堆栈或调用链
- ✅ 敏感信息脱敏后再记录
- ❌ 禁止记录密码、密钥
- ❌ 禁止记录大数组完整内容

### 8.2 性能考虑

- 热路径使用 `SPDLOG_LEVEL(debug)` 条件编译
- 高频日志加采样或节流
- 异步日志避免阻塞主线程

---

## 9. 参考

- [spdlog 文档](https://github.com/gabime/spdlog)
- [CODING_STANDARDS.md](./CODING_STANDARDS.md) 11.1 节