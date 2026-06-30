# LBS Project Superpowers Workflow

版本：v0.1  
日期：2026-06-30  
适用项目：LBS 德州扑克策略引擎

## 1. 总原则

本项目后续全部按 Superpowers 流程推进。

任何新功能、阶段扩展、架构调整，都必须先走：

```text
需求澄清
→ 设计规格 spec
→ 用户确认
→ 实施计划 plan
→ TDD 执行
→ 验证
→ 版本记录
```

不直接跳到写代码，不把多个大模块塞进一个计划。

## 2. 项目当前定位

项目名称：

```text
LBS 德州扑克策略引擎
```

当前定位：

```text
网站当前牌局策略引擎。
用户侧只走数据采集模式。
牌局网站本身不调用 API。
采集器读取当前牌局状态，再交给 LBS 策略引擎分析。
```

当前主文档：

```text
LBS策略引擎开发文档.md
```

当前已生成实施计划：

```text
docs/superpowers/plans/2026-06-30-lbs-v0.1-data-collection-and-single-lbs-lite.md
```

## 3. Superpowers 文件组织

所有后续规格和计划统一放在：

```text
docs/superpowers/specs/
docs/superpowers/plans/
```

命名规则：

```text
spec:
docs/superpowers/specs/YYYY-MM-DD-<stage-or-feature>-design.md

plan:
docs/superpowers/plans/YYYY-MM-DD-<stage-or-feature>.md
```

每个阶段必须至少有：

```text
1 个设计规格 spec
1 个实施计划 plan
1 组测试或验证标准
```

## 4. 阶段拆分

整个项目拆成独立阶段，每个阶段单独走 spec 和 plan。

### V0.1：数据采集 + 单人 LBS-Lite

目标：

```text
跑通从牌局网站采集当前牌局状态，到 LBS 引擎返回基础策略的闭环。
```

范围：

```text
数据采集输入契约
NormalizedState
state_hash 去重
动态动作集合
单人 BTN vs BB 翻牌 LBS-Lite
基础 EV 估算
策略结果输出
回归测试
```

当前状态：

```text
implementation plan 已创建。
等待执行。
```

计划文件：

```text
docs/superpowers/plans/2026-06-30-lbs-v0.1-data-collection-and-single-lbs-lite.md
```

### V0.2：Solver 数据库

目标：

```text
接入 Solver 数据，让 LBS 策略从规则估算升级为 Solver 校准。
```

需要单独创建：

```text
docs/superpowers/specs/YYYY-MM-DD-lbs-v0.2-solver-database-design.md
docs/superpowers/plans/YYYY-MM-DD-lbs-v0.2-solver-database.md
```

范围：

```text
Solver 导入格式
solver_spots 数据结构
局面相似度匹配
Solver 策略和 LBS 策略融合
策略评估集
```

不放进 V0.2：

```text
模型训练
多人已知手牌
完整 Solver
```

### V0.3：更多当前牌局场景

目标：

```text
扩大单人策略引擎覆盖范围。
```

需要单独创建：

```text
docs/superpowers/specs/YYYY-MM-DD-lbs-v0.3-expanded-spots-design.md
docs/superpowers/plans/YYYY-MM-DD-lbs-v0.3-expanded-spots.md
```

范围：

```text
SB vs BB
3Bet pot
Turn 场景
更多牌面结构
更多动作尺度
更多手牌类型
```

### V0.4：多人已知手牌训练研究模式

目标：

```text
支持 1-4 个已知合作方手牌，用于训练研究、内部验证和团队 EV 分析。
```

需要单独创建：

```text
docs/superpowers/specs/YYYY-MM-DD-lbs-v0.4-multi-known-hand-design.md
docs/superpowers/plans/YYYY-MM-DD-lbs-v0.4-multi-known-hand.md
```

范围：

```text
known_hands
team_seats
unknown_seats
objective
known_cards 牌库移除
actor_ev
team_ev
weighted_team_ev
Multi-Hand LBS-Lite
```

分阶段：

```text
先 2 人已知手牌
再 3 人
最后 4 人
```

### V0.5：模型训练

目标：

```text
用 Solver 数据和 LBS 搜索数据训练模型，提高策略速度和泛化能力。
```

需要单独创建：

```text
docs/superpowers/specs/YYYY-MM-DD-lbs-v0.5-model-training-design.md
docs/superpowers/plans/YYYY-MM-DD-lbs-v0.5-model-training.md
```

范围：

```text
Policy Model
Value Model
Belief Model
Multi-Player Value Model
Team Policy Model
Unknown Range Model
模型版本管理
固定评估集
```

### V1.0：产品化稳定版本

目标：

```text
让策略引擎稳定服务网站当前牌局使用。
```

需要单独创建：

```text
docs/superpowers/specs/YYYY-MM-DD-lbs-v1.0-production-engine-design.md
docs/superpowers/plans/YYYY-MM-DD-lbs-v1.0-production-engine.md
```

范围：

```text
采集稳定性
缓存
日志监控
策略版本切换
错误码
回归测试
策略质量看板
性能目标
```

## 5. 每个阶段固定流程

每个阶段都按下面流程执行：

```text
1. 使用 using-superpowers
2. 如涉及新功能或架构，使用 brainstorming
3. 写设计规格 spec
4. 用户确认 spec
5. 使用 writing-plans 写实施计划 plan
6. 用户确认 plan
7. 执行时使用 executing-plans 或 subagent-driven-development
8. 使用 test-driven-development 做核心逻辑
9. 完成前使用 verification-before-completion
10. 记录版本和验证结果
```

## 6. 执行方式选择

每个 plan 完成后，执行方式二选一：

```text
推荐：Subagent-Driven
一个任务一个子代理，任务之间做审查。

备选：Inline Execution
在当前会话逐步执行计划，按检查点验收。
```

如果当前 Codex 环境没有启用 multi-agent，则使用 Inline Execution。

## 7. 阶段准入条件

### 从 V0.1 进入 V0.2

必须满足：

```text
采集器能生成 NormalizedState
单人 BTN vs BB 翻牌可分析
动态动作集合可用
50 个内部固定验证牌局通过
同一状态结果稳定
```

### 从 V0.2 进入 V0.3

必须满足：

```text
能导入 Solver 数据
能命中相似局面
能输出 solver_reference
有 Top action accuracy 基础评估
```

### 从 V0.3 进入 V0.4

必须满足：

```text
单人场景覆盖足够稳定
动作生成和 EV 估算结构可扩展
known_hands 不会破坏单人模式
```

### 从 V0.4 进入 V0.5

必须满足：

```text
多人已知手牌模式有稳定搜索数据
team_ev 输出稳定
训练样本格式固定
```

### 从 V0.5 进入 V1.0

必须满足：

```text
模型有固定评估集
策略质量可量化
延迟和稳定性达到产品化要求
```

## 8. 永久约束

这些约束贯穿整个项目：

```text
采集和策略引擎分离
单人模式和多人模式分离
Solver 数据和模型训练分离
每次策略变化都有版本号
每个阶段都有测试
每个阶段都有回归验证
不在没有 spec 的情况下开发大功能
不把普通用户牌局直接当标准答案训练
```

## 9. 当前下一步

当前推荐下一步：

```text
执行 V0.1 实施计划。
```

计划文件：

```text
docs/superpowers/plans/2026-06-30-lbs-v0.1-data-collection-and-single-lbs-lite.md
```

执行前需要选择：

```text
1. Subagent-Driven：按任务拆给子代理执行和审查
2. Inline Execution：在当前会话按计划逐步执行
```

