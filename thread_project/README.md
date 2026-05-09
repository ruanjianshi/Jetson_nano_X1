# C++ Multithreading Development Test Project

## 项目简介
这是一个完整的 C++ 多线程开发测试项目，包含各种多线程同步原语的详细测试和开发日志。

## 项目结构
```
ThreadPoolProject/
├── include/
│   └── Logger.h                    # 日志记录器
├── src/
│   └── main.cpp                    # 主程序
├── tests/
│   ├── thread_management/
│   │   └── ThreadTest.h           # 线程管理测试
│   ├── mutex/
│   │   └── MutexTest.h            # 互斥锁测试
│   ├── condition/
│   │   └── ConditionTest.h        # 条件变量测试
│   ├── semaphore/
│   │   └── SemaphoreTest.h        # 信号量测试
│   ├── rwlock/
│   │   └── RWLockTest.h           # 读写锁测试
│   └── tls/
│       └── TLSTest.h              # 线程局部存储测试
├── logs/
│   └── development.log            # 开发日志（自动生成）
├── build/                         # 构建输出
├── CMakeLists.txt
├── Makefile
└── README.md
```

## 测试模块

### 1. 线程管理 (Thread Management)
- 基本线程创建
- 获取线程 ID
- 线程返回值
- 分离线程 (detach)
- 多线程并行

### 2. 互斥锁 (Mutex)
- 基本互斥锁
- lock_guard RAII
- unique_lock 灵活锁
- try_lock 尝试加锁
- recursive_mutex 递归锁

### 3. 条件变量 (Condition Variable)
- 基本条件等待
- notify_all 通知所有
- 生产者-消费者模式

### 4. 信号量 (Semaphore)
- 计数信号量
- 二进制信号量
- try_acquire 尝试获取

### 5. 读写锁 (Read-Write Lock)
- 多读者并发
- 写者独占访问
- 读写冲突处理
- try_lock 尝试

### 6. 线程局部存储 (Thread Local Storage)
- thread_local 变量
- TLS 与类
- TLS vs 全局变量

## 编译运行

### 使用 Makefile
```bash
make run        # 交互式运行
make test       # 自动运行所有测试
make clean      # 清理构建文件
```

### 使用 CMake
```bash
mkdir -p build
cd build
cmake ..
make
./multithread_test
```

## 使用说明
程序启动后会显示菜单，你可以选择：
- 运行单个模块的测试
- 运行所有测试
- 查看开发日志 (logs/development.log)

## 系统要求
- C++20 或更高版本
- pthread 库
- CMake 3.10+ (可选)

## 日志
所有测试输出会同时显示在控制台和写入 `logs/development.log` 文件。