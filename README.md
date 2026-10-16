# Perfmon V3

Perfmon 是一个轻量级、配置驱动的本机任务监控与执行框架。它由多个 Source 发现任务，由 Broker 将任务分配给 Worker 进程，Worker 按 Workflow 配置串行执行步骤，最后由 Sink 批量或定时提交结果。

## 核心概念

| 概念 | 职责 |
| --- | --- |
| Source | 任务触发器。轮询、定时或监听外部事件，产生 JobRequest。 |
| JobRequest | 一次任务请求，包含 job_id、Workflow 名称、来源和运行参数。 |
| Workflow | 一个完整的业务流程，由多个 Step 按顺序组成。 |
| Step / Runner | Workflow 中的一个执行步骤。 |
| Broker | 任务调度器。维护待执行任务、Worker 状态和运行中任务，并主动分配任务。 |
| Worker | 一个独立的 Python 进程，负责执行 Broker 分配的 JobRequest。 |
| Supervisor | 负责启动、监控、停止和重启 Worker。 |
| Sink | 结果提交器。可将结果输出到终端、文件、HTTP 服务等目的地。 |
| Registry | 记录组件名称和动态加载位置的注册表。 |

## 运行链路

```text
Source
  └─> JobRequest
        └─> Broker
              └─> 空闲 Worker（独立 Pipe）
                    └─> Workflow
                          └─> Step / Runner 1 -> Step / Runner 2 -> ...
                                └─> JobResult
                                      └─> SinkManager
                                            └─> Sink（print / file / http ...）
```

## 计划支持的能力

- JSON 配置驱动的 Source、Workflow、Runner 和 Sink。
- 多个 Source 并行运行并产生任务。
- Broker 统一调度，支持容量限制、优先级、排队和背压。
- 多 Worker 进程并行执行，避免共享任务通道产生隐式竞争。
- Workflow 内多个 Runner 串行执行，并传递中间结果。
- Runner 负责生成最终业务结构；执行层负责 timeout、异常捕获和 retry，提交前再由结果校验层执行必要的内容检查。
- `reenterable` 防重入策略。
- Worker 异常退出检测、任务恢复和进程重启。
- Sink 的缓冲、容量触发、超时触发和失败恢复。
- 统一日志格式、优雅停止和运行状态监控。

## 当前状态

项目仍处于核心架构实现阶段。当前已经完成协议模型、组件 Registry、Runner/StepExecutor、WorkflowExecutor、结果校验层、单 Worker Pipe 通信和最小 CLI 骨架；Broker 调度、配置加载、Source、Sink 和完整 CLI 装配仍在实现中。

项目目标、术语和阶段计划见 [PROJECT.md](PROJECT.md)。Agent 的协作和代码修改规范见 [AGENTS.md](AGENTS.md)。

## 运行环境

- Python 3.15 或更高版本。
- 默认使用普通 CPython 构建；free-threaded 构建作为后续实验运行时单独验证。
- 依赖安装到项目虚拟环境中，不污染系统 Python。

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```
