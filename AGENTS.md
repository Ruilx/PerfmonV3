# Perfmon V3 Agent 工作规范

## 1. 项目定位

Perfmon V3 是一个 Python 配置驱动任务执行框架。修改代码时，应优先维护任务协议、进程生命周期和异常恢复的正确性，再考虑增加业务组件。

所有代码和设计以本项目当前目标为准。

## 2. 目录职责

- `src/base/`：稳定的基础抽象，例如 `ExecutableBase`、`SourceBase`、`RunnerBase`、`SinkBase`。
- `src/core/`：运行时核心，例如 Broker、Worker、Supervisor、异步运行时、日志和计时器。
- `src/core/registry/`：Source、Runner、Sink 等组件注册和动态加载。
- `src/components/`：具体 Source、Runner、Sink 实现。
- `src/config/`：配置模型和配置校验。
- `tests/`：单元测试、协议测试、故障恢复测试。
- `runtime/`：运行时输出，不提交日志、缓存或临时文件。

当前目录结构尚未完全迁移完成；新增文件时应逐步向上述职责靠拢。

## 3. 核心命名

- `JobRequest`：一次运行请求。
- `Workflow`：完整任务流程。
- `Step`：流程中的一个步骤。
- `Runner`：执行步骤的组件。
- `Worker`：承载任务的子进程。
- `Broker`：主动分配任务的调度器。
- `Supervisor`：管理 Worker 生命周期。
- `Sink`：提交结果的组件。
- `Source`：产生任务的组件。

不要在新代码中混用 `job`、`workflow`、`step` 表示同一个层级。核心协议必须使用稳定、明确的字段名。

项目运行基线为 Python 3.15+，默认使用普通 CPython 构建。优先使用现代标准库和类型语法，不为旧 Python 版本增加兼容分支；free-threaded 构建需要单独验证，不能默认假设第三方依赖完全兼容。

## 4. 修改原则

1. 先阅读 `PROJECT.md` 和相关模块，再修改代码。
2. 任务协议优先于组件实现；先定义输入、输出、状态和错误语义。
3. Broker 通过显式状态和独立通信通道调度 Worker。
4. 不依赖运行库的私有状态来维持进程调度正确性。
5. 不把不可序列化的实例、锁、事件循环对象直接传入 spawn 子进程。
6. 所有 Worker 都必须有明确的启动、就绪、停止、异常退出状态。
7. 所有外部副作用都要考虑重试和重复执行。
8. 组件 Registry 负责解析和类型校验，不负责业务实例的长生命周期管理。
9. 尽量使用类型注解和明确的数据结构；跨进程消息优先使用普通 dict 或 dataclass 转换后的 dict。
10. 名称必须表达稳定的业务层级，不为了短小保留含义不清的缩写。

## 5. 异步与事件驱动约定

可根据问题选择 `asyncio`、`async/await`、线程、进程或普通函数调用。现有事件循环组件不是必须保留的兼容层；如果标准库的异步方案更清晰，应直接采用并重构或删除旧组件。

无论采用哪种方式，都不能让阻塞的文件、HTTP、Shell 或第三方库调用阻塞不应被阻塞的调度线程。异步边界、取消语义和资源清理必须明确。

## 6. 测试要求

涉及以下内容时必须增加或更新测试：

- JobRequest/JobResult 字段。
- Broker 的排队和分配。
- Worker 崩溃、重启和任务恢复。
- timeout、retry、reenterable。
- Source 停止和 Sink 缓冲刷新。
- Windows spawn 兼容性。

提交前至少执行：

```powershell
python -m compileall -q src
python -m unittest discover -v
```

如果项目依赖尚未安装，直接在项目虚拟环境中使用 `pip` 或 `uv` 安装，并同步更新 `requirements.txt`。如果测试命令仍不可用，应在交付说明中明确记录，不要把未验证的结果描述为已通过。

## 7. 文档要求

- 项目目标和架构变化写入 `PROJECT.md`。
- 面向使用者的功能和运行说明写入 `README.md`。
- Agent 的操作约束写入本文件。
- 重大协议变化应同时更新消息示例和测试。
