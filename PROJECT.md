# Perfmon V3 项目规划

## 1. 项目目标

Perfmon V3 的目标是构建一个轻量级、配置驱动、可扩展且具备可靠进程调度能力的本机任务执行框架。

代码和文档只围绕当前目标组织：

1. 明确 Job、Workflow、Step、Worker 等概念。
2. 用 Broker 主动分配任务，避免多个进程竞争共享任务通道。
3. 将进程生命周期、任务调度、业务执行和结果提交分离。
4. 为异常恢复、超时、重试和幂等执行建立明确协议。

## 1.1 运行时基线

- 目标 Python 版本：3.15+。
- 新代码可以使用 Python 3.15 的标准语法、类型系统和标准库能力。
- 只支持 Python 3.15+，不增加旧 Python 版本兼容分支。
- 默认使用普通 CPython 构建；free-threaded 构建在核心功能稳定后作为独立测试目标。
- 第三方依赖安装在项目虚拟环境中，并同步维护 `requirements.txt`。

## 2. 术语约定

### 2.1 任务层级

```text
Source 产生 JobRequest
  JobRequest 指向一个 Workflow
    Workflow 由多个 Step 组成
      Step 由具体 Runner 实现
```

- `JobRequest`：一次实际运行请求，必须有唯一 `job_id`。
- `Workflow`：配置中的完整业务流程。
- `Step`：Workflow 中的一个执行步骤。
- `Runner`：执行 Step 的可插拔组件。
- `JobResult`：Workflow 最终产生的结果。

### 2.2 Step 的执行边界

具体 Runner 负责产生并组织最终的业务结果，同时管理自己的资源。统一的 `StepExecutor` 只负责执行边界：

```text
Runner.run(params)
  -> StepResult
```

StepExecutor 负责调用 Runner、记录耗时、捕获异常、执行 timeout 和 retry，并将错误转换为统一的 StepResult。结果提交前由独立的结果校验层执行必要的内容、可序列化性或目标端格式检查；校验结果应明确区分可重试和不可重试失败。

### 2.3 运行层级

- `Source`：只负责发现和产生 JobRequest，不负责执行任务。
- `Broker`：只负责任务排队、选择 Worker 和维护任务状态。
- `Worker`：只负责承载一个子进程和一个独立通信通道。
- `WorkerRuntime`：运行在子进程内部，负责接收和执行任务。
- `Supervisor`：负责 Worker 的启动、监控、停止和重启。
- `Sink`：只负责结果提交和提交失败恢复。

## 3. 目标架构

```text
                         +----------------+
                         |  SourceManager |
                         +--------+-------+
                                  |
                                  v
                         +----------------+
                         |     Broker     |
                         | pending/running|
                         +---+--------+---+
                             |        |
                 dedicated   |        |   dedicated
                    Pipe      v        v      Pipe
                         +---------+  +---------+
                         | Worker 0|  | Worker 1|
                         +----+----+  +----+----+
                              |            |
                              +-----+------+
                                    v
                              +-----------+
                              | JobResult |
                              +-----+-----+
                                    v
                              +-----------+
                              | SinkManager|
                              +-----------+
```

Worker 不共享同一个任务通道。Broker 为每个 Worker 保存独立的控制通道，只向空闲 Worker 分配任务。

## 4. 消息协议原则

### JobRequest

```python
{
    "type": "job_request",
    "job_id": "uuid",
    "workflow": "workflow_name",
    "source": "source_name",
    "params": {},
    "priority": 10,
    "attempt": 1,
}
```

### Worker 事件

```python
{
    "type": "job_started | job_finished | job_failed | worker_ready",
    "worker_id": "worker_0",
    "job_id": "uuid",
    "attempt": 1,
    "result": {},
    "error": {},
}
```

协议中的字段必须保持稳定。统一使用 `workflow` 表示流程名称，使用 `job_id` 表示一次运行。

## 5. 可靠性原则

### 5.1 任务投递

默认采用“至少一次投递 + job_id 幂等”策略。Worker 可能在已经产生外部副作用、但尚未回报完成事件时崩溃，因此不能假设严格 exactly-once。

### 5.2 Worker 崩溃

Broker 必须记录 `running_jobs`。Worker 异常退出时：

1. 标记 Worker 为 `DEAD`。
2. 找到该 Worker 上的运行中任务。
3. 按 retry policy 决定重新排队或生成失败结果。
4. 由 Supervisor 重启 Worker。
5. 新 Worker 就绪后继续调度。

### 5.3 防重入

`reenterable=False` 时，由 Broker 维护 Workflow 的运行状态。默认策略是同一 Workflow 已运行时跳过新请求；后续可扩展为排队或合并。

### 5.4 超时

任务超时由 Broker/ Supervisor 负责观察。需要硬超时时，允许终止整个 Worker 并重新启动，避免无法杀死的 Python 线程继续占用 Worker。

## 6. 组件与 Registry

核心组件名称固定为：

| 组件 | 职责 |
| --- | --- |
| `RunnerRegistry` | 注册和加载 Runner |
| `SourceRegistry` | 注册和加载 Source |
| `SinkRegistry` | 注册和加载 Sink |
| `ComponentSpec` | 描述组件的模块路径和类名 |
| `RegistryBase` | 提供统一的注册、查找和类型校验能力 |

Registry 只负责名称到组件类的解析和类型校验，不负责实例生命周期。

## 7. 实现路线

### 当前可以开始实现

| 优先级 | 组件 | 原因 |
| --- | --- | --- |
| P0 | `JobRequest`、`JobResult`、`WorkerEvent` | 所有模块都依赖的稳定消息协议。 |
| P0 | `ComponentSpec`、`RegistryBase`、三类 Registry | 隔离动态加载和业务执行。 |
| P0 | `RunnerBase`、`StepExecutor`、`WorkflowExecutor` | 不依赖多进程即可完整单测业务语义。 |
| P1 | 配置模型和日志 | 为运行时组装提供明确入口。 |

### 第二批实现

| 优先级 | 组件 | 原因 |
| --- | --- | --- |
| P1 | `WorkerRuntime`、`WorkerHandle` | 先建立单 Worker 的通信协议。 |
| P1 | `Supervisor` | 管理 Worker 启动、停止、异常和重启。 |
| P1 | `Broker` | 在 Worker 协议稳定后实现调度和背压。 |

### 第三批实现

| 优先级 | 组件 | 原因 |
| --- | --- | --- |
| P2 | Scheduler Source | 接入实际任务产生机制。 |
| P2 | Sink、SinkManager | 接入结果缓冲和外部提交。 |
| P2 | CLI 和完整配置装配 | 最后连接全部运行时组件。 |

## 8. 阶段计划

### Phase 0：基础约定

- 固定 Python 3.15+ 运行基线和依赖管理方式。
- 固定术语、目录和消息协议。
- 修复 V3 当前无法编译的问题。
- 补齐配置加载、日志和基础生命周期接口。

### Phase 1：业务域迁移

- 实现 Workflow、JobRequest、JobResult。
- 实现 `RunnerBase`、`StepExecutor` 和 Workflow 执行器。
- 实现常量值、命令执行、文件读取等基础 Runner。
- 完善 Runner 输出模型、结果校验和可重试失败策略。

### Phase 2：Worker 与 Broker

- 实现 WorkerHandle、WorkerRuntime。
- 每个 Worker 使用独立 Pipe。
- 实现空闲 Worker 分配、任务排队、结果回报和崩溃恢复。

### Phase 3：Source

- 实现 Scheduler Source。
- Source 通过 Broker 提交 JobRequest。
- 支持 priority、周期调度和停止。

### Phase 4：Sink

- 实现 SinkBase 和 SinkManager。
- 实现 terminal、file、http Sink。
- 保留 buffer capacity 和 timeout 触发机制。

### Phase 5：Supervisor 与 CLI

- 实现 Worker 监控和优雅关闭。
- 完成配置模型和配置校验。
- 接入信号、日志和状态输出。

### Phase 6：故障测试

- Worker 执行中崩溃。
- Worker 完成任务后、回报前崩溃。
- 任务超时。
- Broker 队列满。
- Sink 发送失败。
- 优雅停止时存在 pending/running 任务。
- Windows spawn 模式。

## 9. 当前进度

已完成第一批 P0 基础：

- `JobRequest`、`JobResult`、`StepResult`、`WorkerEvent` 协议模型。
- `ComponentSpec`、`RegistryBase`、Runner/Source/Sink Registry。
- `RunnerBase`、`StepExecutor`、`WorkflowDefinition`、`WorkflowExecutor`。
- 最小 `ValueRunner` 和协议/Workflow 单元测试。
- `ResultValidator` 以及可区分可重试性的提交前校验结果。
- `WorkerRuntime`、`WorkerHandle` 和 Windows spawn 下的单 Worker Pipe 测试。
- Python 3.15 虚拟环境和依赖安装。

## 10. 当前已知问题

V3 当前属于半成品骨架，尚未完成：

- `main.py` 的 CLI 实现。
- Broker 的任务分配和 Worker 状态机。
- Worker 的 Pipe 通信和 Job 执行循环。
- 完整配置模型和运行时装配。
- 命令执行、文件读取等业务 Runner。
- Source、Sink 和结果缓冲。
- 完整测试和 Windows spawn 验证。
