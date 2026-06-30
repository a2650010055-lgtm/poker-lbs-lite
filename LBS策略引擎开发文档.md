# LBS 德州扑克策略引擎开发文档

版本：v0.1  
日期：2026-06-30  
定位：网站当前牌局策略引擎，用户侧只使用数据采集接入；网站不调用 API，不是完整 Solver。

## 1. 项目目标

本项目要做的是一个可为网站当前牌局提供策略结果的德州扑克策略引擎。

牌局网站本身不调用 API。系统通过数据采集器读取网页中的当前牌局状态，再交给 LBS 策略引擎分析。

核心目标：

- 用户在网站内进入或使用一个当前牌局。
- 系统通过数据采集方式获得当前牌局状态。
- 后台 LBS 策略引擎返回推荐动作、动作频率、EV、置信度和关键原因。
- 后期通过 Solver 数据和模型训练，让策略覆盖越来越多场景，准确度越来越高。

一句话定义：

```text
LBS Strategy Engine = 网站当前牌局的德州扑克策略大脑
```

## 2. 产品边界

### 2.1 要做什么

- 当前牌局策略分析。
- 牌局状态标准化。
- 对手范围推断。
- 简化策略树搜索。
- EV 计算。
- Solver 数据库校准。
- 策略结果输出。
- 数据采集接入模式。
- 牌局状态去重和校验。
- 后期训练 Belief / Policy / Value 模型。

## 3. 总体架构

```text
唯一用户侧接入方式：数据采集

牌局网站页面
  ↓
数据采集器
  ↓
牌局状态解析器
  ↓
状态去重 / 合法性校验
  ↓
LBS 内部分析入口
  ↓
牌局标准化模块
  ↓
LBS 策略引擎
  ├── 手牌评估模块
  ├── 胜率/赔率模块
  ├── Belief 对手范围模块
  ├── Strategy Tree 策略树模块
  ├── EV 计算模块
  ├── Solver 策略数据库
  ├── Policy / Value / Belief 模型
  └── 结果解释模块
  ↓
返回 JSON 策略结果
  ↓
策略结果面板 / 后台页面展示
```

推荐技术栈：

```text
策略服务：Python，可先用进程内调用，后期再封装内部服务
策略引擎：Python
数据库：PostgreSQL
缓存：Redis
模型训练：PyTorch
Solver 数据来源：GTO+ / PioSOLVER
网站前端：React / Next.js
数据采集器：Chrome Extension / Playwright / 页面内状态对象
```

## 4. LBS 是什么

LBS 不是一个窗口，也不是单独软件。

它在本项目中以后台算法模块存在：

```text
Belief：猜对手范围
Search：展开策略树
Value：计算或预测 EV
```

完整流程：

```text
输入当前牌局
→ 推断对手范围
→ 展开当前可选动作
→ 展开对手可能回应
→ 估算每条路线 EV
→ 输出推荐策略
```

## 5. MVP 范围

第一版不要做全量德州扑克。

建议 MVP 只支持：

```text
牌局类型：现金局
人数：单挑底池
位置：BTN vs BB
阶段：翻牌 Flop
筹码：100BB
动作集合：动态生成，不固定为三个动作
无人下注时：check / bet_33 / bet_75
面对下注时：fold / call / raise_3x
V0.2 增加：all_in
输出内容：推荐动作、动作频率、EV、置信度、简短原因
```

MVP 成功标准：

- 采集器能读取当前牌局并触发 LBS 分析。
- 同一个输入能稳定返回同一个策略结果。
- 返回结果包含动作频率和 EV。
- 至少覆盖 50 个常见翻牌面类型。
- 每次策略响应控制在 1-3 秒内。

## 6. 核心分析数据格式

### 6.1 分析单手牌

内部分析入口：

```text
analyze_hand(state)
```

输入示例：

```json
{
  "game_type": "cash",
  "street": "flop",
  "position": "BTN_vs_BB",
  "hero_hand": ["Ah", "Kh"],
  "board": ["Kc", "8d", "3s"],
  "pot": 100,
  "effective_stack": 900,
  "action_history": [
    {"player": "BTN", "action": "raise", "size": 2.5},
    {"player": "BB", "action": "call"},
    {"player": "BB", "action": "check"}
  ]
}
```

返回示例：

```json
{
  "recommend": "bet_33",
  "strategy": {
    "check": 0.25,
    "bet_33": 0.65,
    "bet_75": 0.10
  },
  "ev": {
    "check": 15.2,
    "bet_33": 24.6,
    "bet_75": 18.1
  },
  "confidence": 0.78,
  "reason_codes": [
    "top_pair_top_kicker",
    "dry_board",
    "range_advantage",
    "small_bet_gets_value"
  ],
  "summary": "推荐下注 33%。该牌面较干燥，你有顶对顶踢脚，小下注可以从更差的 Kx、8x 和中对拿价值。"
}
```

### 6.2 内部批量评估

后期增加：

```text
analyze_hands_batch(states)
```

用途：

- 内部评估策略引擎。
- 回归测试策略版本。
- 生成测试报告。

说明：

```text
该能力不作为网站用户侧主功能。
网站主要用于当前牌局的单局使用和策略展示。
批量能力只用于内部质量评估、策略版本对比和数据生产。
```

## 7. 核心模块说明

### 7.1 牌局标准化模块

职责：

- 校验手牌和公共牌是否合法。
- 判断当前街道。
- 统一位置格式。
- 统一下注历史格式。
- 计算 pot、SPR、有效筹码。

输出：

```text
NormalizedState
```

### 7.2 手牌评估模块

职责：

- 判断当前牌型。
- 判断听牌类型。
- 计算 outs。
- 估算当前胜率。
- 识别牌面结构。

牌面结构示例：

```text
A 高干燥面
K 高干燥面
低连张湿润面
同花听牌面
对子面
单高张彩虹面
```

### 7.3 Belief 对手范围模块

职责：

- 根据位置和行动历史推断对手范围。
- 输出对手手牌组合概率。

第一版使用规则表：

```text
BB call BTN open:
包含 KQs、KJs、QJs、JTs、Axs、中小对子等
减少 AA、KK、QQ、AK，因为这些牌更常 3Bet
```

后期升级为 Belief Model：

```text
输入：牌局状态 + 行动历史
输出：169 起手牌矩阵或 1326 combo 概率
```

### 7.4 策略树模块

职责：

- 根据当前状态生成可选动作。
- 展开对手可能回应。
- 搜索 1-2 层后续分支。

动作集合不是固定三个动作，必须根据当前局面动态生成。

如果前面没人下注：

```text
合法动作：
- check
- bet_33
- bet_75

V0.2 增加：
- all_in
```

如果前面已经有人下注：

```text
合法动作：
- fold
- call
- raise_3x

V0.2 增加：
- all_in
```

对手回应动作：

```text
面对我方下注：
- fold
- call
- raise_3x

面对我方过牌：
- check
- bet_33
- bet_75
```

早期不要一次性加入太多下注尺度，因为动作越多，策略树分支越大。

分阶段动作规划：

```text
V0.1：
无人下注：check / bet_33 / bet_75
面对下注：fold / call / raise_3x

V0.2：
加入 all_in

V0.3：
加入 bet_25 / bet_50 / bet_100 / raise_2_5x / raise_pot

V1.0：
根据底池、SPR、有效筹码和当前下注额动态生成动作集合
```

策略树示例一：无人下注

```text
当前局面
├── check
│   ├── villain check
│   └── villain bet
├── bet_33
│   ├── villain fold
│   ├── villain call
│   └── villain raise_3x
└── bet_75
    ├── villain fold
    ├── villain call
    └── villain raise_3x
```

策略树示例二：面对下注

```text
当前局面：villain bet
├── fold
├── call
└── raise_3x
    ├── villain fold
    ├── villain call
    └── villain all_in
```

### 7.5 EV 计算模块

职责：

- 计算每个动作的期望收益。
- 结合胜率、弃牌率、跟注范围、加注范围。
- 对无法完整搜索的节点调用 Value Model 或规则估值。

简化 EV 公式示意：

```text
EV(bet) =
  fold_prob * pot
  + call_prob * equity_when_called * final_pot
  - call_prob * bet_size
  - raise_prob * loss_or_continue_cost
```

### 7.6 Solver 策略数据库

职责：

- 存储 GTO+ / PioSOLVER 跑出的标准策略。
- 按场景检索相似局面。
- 校准 LBS 搜索结果。

建议字段：

```text
position
street
stack_depth
spr
board_cards
board_texture
hero_hand_class
action_history
solver_policy
solver_ev
source_solver
solver_version
created_at
```

### 7.7 模型模块

后期训练 3 个模型：

```text
Belief Model：预测对手范围
Policy Model：预测动作频率
Value Model：预测 EV
```

上线后流程：

```text
Belief Model 猜范围
→ Policy Model 给初步策略
→ Value Model 估值
→ LBS 小树搜索修正
→ 返回最终策略
```

### 7.8 多人已知手牌训练研究模式

该模式用于私有训练、策略研究和引擎测试。

核心思想：

```text
系统可以输入 1-4 个已知合作方手牌。
引擎从牌库中移除这些已知牌。
再推断未知玩家范围。
最后计算当前行动玩家策略、个人 EV 和团队 EV。
```

该模式不是普通单人 GTO 策略。普通模式只知道 Hero 手牌；多人已知手牌模式会利用多个已知手牌带来的阻断牌信息。

#### 7.8.1 支持人数

```text
1 人已知：普通单人模式
2 人已知：优先支持，可行性最高
3 人已知：中期支持，团队 EV 更复杂
4 人已知：后期支持，需要限制搜索深度和动作数量
```

#### 7.8.2 输入结构

示例：

```json
{
  "mode": "multi_known_hand_research",
  "table_size": 6,
  "current_actor": "seat_1",
  "team_seats": ["seat_1", "seat_3", "seat_5"],
  "known_hands": {
    "seat_1": ["Ah", "Kh"],
    "seat_3": ["Qd", "Qs"],
    "seat_5": ["9h", "9c"]
  },
  "unknown_seats": ["seat_2", "seat_4", "seat_6"],
  "board": ["Kc", "8d", "3s"],
  "pot": 100,
  "effective_stacks": {
    "seat_1": 900,
    "seat_2": 850,
    "seat_3": 1000,
    "seat_4": 780,
    "seat_5": 920,
    "seat_6": 1100
  },
  "objective": "team_ev"
}
```

`objective` 可选：

```text
actor_ev：最大化当前行动玩家 EV
team_ev：最大化合作方总 EV
weighted_team_ev：按权重最大化团队 EV
```

#### 7.8.3 输出结构

示例：

```json
{
  "current_actor": "seat_1",
  "recommend": "bet_33",
  "strategy": {
    "check": 0.22,
    "bet_33": 0.61,
    "bet_75": 0.17
  },
  "ev": {
    "seat_1": 18.4,
    "seat_3": 4.2,
    "seat_5": 1.1,
    "team": 23.7
  },
  "objective": "team_ev",
  "confidence": 0.72
}
```

#### 7.8.4 多人模式计算流程

```text
1. 采集当前牌局状态
2. 读取 1-4 个已知手牌
3. 从牌库移除所有已知牌
4. 推断未知玩家范围
5. 判断当前行动玩家
6. 动态生成合法动作
7. 展开当前行动玩家策略树
8. 模拟未知玩家回应
9. 计算每条路线：
   - 当前玩家 EV
   - 每个合作方 EV
   - 团队总 EV
10. 根据 objective 输出策略
```

#### 7.8.5 多人模式训练路线

不要一开始直接训练多人合作模型。先做 Multi-Hand LBS-Lite，再用搜索结果生成训练数据。

训练路线：

```text
阶段 1：多手牌胜率和阻断牌计算
阶段 2：2 人已知手牌 Multi-Hand LBS-Lite
阶段 3：3 人已知手牌团队 EV
阶段 4：4 人已知手牌受限搜索
阶段 5：训练 Multi-Player Value Model
阶段 6：训练 Team Policy Model
阶段 7：训练 Unknown Range Model
```

模型说明：

```text
Unknown Range Model：
预测未知玩家范围。

Multi-Player Value Model：
预测每个合作方 EV 和团队 EV。

Team Policy Model：
根据当前行动玩家、已知手牌和团队目标输出动作频率。
```

#### 7.8.6 可行性判断

```text
2 人已知手牌胜率分析：很高
2 人团队 EV LBS-Lite：高
3 人团队 EV LBS-Lite：中高
4 人团队 EV LBS-Lite：中
完整多人合作 Solver：低
模型化多人合作策略：中，需要先积累搜索数据
```

推荐路线：

```text
先做 1 人普通模式
→ 再做 2 人已知手牌模式
→ 再扩展 3 人
→ 最后支持 4 人
```

## 8. 策略计算工作流

### 8.1 在线分析流程

```text
采集器读取当前牌局
↓
校验采集状态
↓
牌局标准化
↓
识别牌力、牌面、SPR
↓
Belief 模块推断对手范围
↓
查询 Solver 策略数据库
↓
如果命中高相似局面：
  使用 Solver 策略作为主参考
否则：
  使用 LBS-Lite 策略树搜索
↓
计算动作 EV
↓
生成策略频率
↓
生成 reason_codes
↓
返回 JSON
```

### 8.2 数据采集接入流程

牌局网站不能主动调用 API，因此使用旁路数据采集模式。

核心思路：

```text
牌局网站不需要改成主动请求 LBS。
采集器像观察员一样读取当前牌局状态。
采集器把牌局状态转成标准 JSON。
然后由采集器或中间服务交给 LBS 策略引擎。
```

整体流程：

```text
牌局网站页面
↓
数据采集器读取牌局状态
↓
状态解析器提取手牌、公共牌、底池、筹码、行动历史
↓
转换为 NormalizedState
↓
状态去重，避免同一局面重复分析
↓
提交给内部分析入口
↓
LBS 引擎返回策略
↓
策略结果展示在侧边栏、后台页面或测试面板
```

#### 8.2.1 推荐采集方式

优先级从高到低：

```text
1. 页面状态对象采集
2. DOM 元素采集
3. Hand history / 日志导入
4. Canvas / OCR 图像识别
```

#### 8.2.2 页面状态对象采集

如果牌局网站是自己可控的，推荐在页面里维护一个全局状态对象。

示例：

```js
window.__POKER_STATE__ = {
  street: "flop",
  hero_hand: ["Ah", "Kh"],
  board: ["Kc", "8d", "3s"],
  position: "BTN_vs_BB",
  pot: 100,
  effective_stack: 900,
  action_history: [
    { player: "BTN", action: "raise", size: 2.5 },
    { player: "BB", action: "call" },
    { player: "BB", action: "check" }
  ],
  updated_at: 1782816000000
}
```

采集器定时读取：

```text
window.__POKER_STATE__
```

优点：

- 最稳定。
- 不需要识别图片。
- 不依赖页面样式。
- 状态字段可控。

缺点：

- 需要能修改牌局网站代码。

#### 8.2.3 DOM 元素采集

如果页面中的牌、底池、筹码、行动记录是普通 HTML 元素，可以通过浏览器插件或脚本读取。

采集内容：

```text
hero_hand
board
pot
effective_stack
seat_positions
current_player
action_history
```

实现方式：

```text
Chrome Extension Content Script
或
Playwright 采集脚本
```

优点：

- 不一定需要改测试网站。
- 采集成本较低。

缺点：

- 页面结构变化后需要维护选择器。
- 如果牌桌是 canvas 渲染，DOM 可能读不到真实牌局数据。

#### 8.2.4 Hand history / 日志导入

如果测试网站可以导出历史牌局，优先解析日志。

适合场景：

- 内部批量评估。
- 回放分析。
- 策略引擎评估。

优点：

- 数据完整。
- 稳定性高。
- 适合内部批量跑策略。

缺点：

- 不适合实时观察页面状态。
- 需要定义日志格式解析器。

#### 8.2.5 Canvas / OCR 图像识别

如果牌桌是 canvas 或图片渲染，并且无法读取 DOM 或状态对象，则考虑 OCR / 图像识别。

流程：

```text
定时截图
↓
裁剪手牌区域、公共牌区域、底池区域、筹码区域
↓
识别牌面和数字
↓
转换成标准牌局状态
↓
调用 LBS
```

优点：

- 对无法读取 DOM 的页面也可能可用。

缺点：

- 开发难度高。
- 识别错误率需要控制。
- 页面分辨率、主题、动画都会影响准确率。

建议：

```text
只作为最后方案，不作为 MVP 首选。
```

#### 8.2.6 状态去重

采集器会频繁读取页面，因此必须做状态去重。

推荐生成状态指纹：

```text
state_hash = hash(
  street
  + hero_hand
  + board
  + pot
  + effective_stack
  + action_history
)
```

如果 `state_hash` 没变化，不重复调用 LBS。

#### 8.2.7 采集模式下的展示方式

可选展示方式：

```text
1. 独立后台页面
2. 浏览器插件侧边栏
3. 测试网站内嵌调试面板
4. 本地控制台 / 管理面板
```

MVP 推荐：

```text
独立后台页面 + 采集器提交状态
```

原因：

- 不强依赖原网站 UI。
- 开发快。
- 后期容易扩展。

### 8.3 Solver 数据生产流程

```text
选择高频场景
↓
用 GTO+ / PioSOLVER 跑解
↓
导出策略频率和 EV
↓
清洗成统一格式
↓
标注牌面类型和手牌类型
↓
写入 Solver 策略数据库
↓
加入评估集
```

第一批建议跑：

```text
BTN vs BB SRP
SB vs BB SRP
BTN vs BB 3Bet Pot
K 高干燥面
A 高干燥面
低连张湿润面
同花听牌面
对子面
```

### 8.4 模型训练流程

```text
Solver 标准答案
+ LBS 搜索结果
+ 人工审核样本
↓
构建训练集
↓
训练 Policy Model
↓
训练 Value Model
↓
训练 Belief Model
↓
使用固定评估集对比上一版本
↓
通过后发布新策略版本
```

训练数据不能直接使用普通用户打法作为标准答案。

普通用户数据更适合用于：

- 找高频测试场景。
- 发现系统覆盖盲区。
- 收集输入格式和异常案例。
- 做产品使用分析。

## 9. 数据库设计草案

### 9.1 hand_analysis_logs

记录每次采集分析。

```text
id
request_state_json
response_strategy_json
engine_version
latency_ms
created_at
```

### 9.2 solver_spots

记录 Solver 结果。

```text
id
position
street
stack_depth
spr
board_cards
board_texture
hero_hand_class
action_history_hash
solver_policy_json
solver_ev_json
source
created_at
```

### 9.3 range_profiles

记录默认范围表。

```text
id
scenario
position
action_line
range_matrix_json
version
created_at
```

### 9.4 model_versions

记录模型版本。

```text
id
model_type
version
training_dataset_id
metrics_json
artifact_path
status
created_at
```

### 9.5 collected_states

记录从测试网站采集到的牌局状态。

```text
id
source_site
source_mode
raw_state_json
normalized_state_json
state_hash
parse_status
parse_error
created_at
```

`source_mode` 可选：

```text
window_state
dom
hand_history
ocr
manual
```

### 9.6 collector_events

记录采集器运行事件。

```text
id
collector_id
event_type
payload_json
created_at
```

用途：

- 调试采集异常。
- 判断页面结构是否变化。
- 追踪状态重复提交问题。

## 10. 版本路线图

### V0.1：LBS-Lite 引擎

目标：跑通数据采集到策略分析的闭环。

功能：

- `analyze_hand(state)`
- 输入校验
- 翻牌 BTN vs BB
- 规则范围表
- 简化策略树
- EV 估算
- JSON 返回

### V0.2：Solver 数据库

目标：提高策略准确度。

功能：

- Solver 数据导入工具
- Solver 策略表
- 相似局面查询
- LBS + Solver 混合策略输出

### V0.3：更多场景

目标：扩大覆盖。

功能：

- SB vs BB
- 3Bet pot
- Turn 场景
- 更多牌面结构
- 更多手牌类型

### V0.4：多人已知手牌研究模式

目标：支持 1-4 个已知合作方手牌的训练研究分析。

功能：

- `known_hands`
- `team_seats`
- `unknown_seats`
- `objective`
- 牌库移除和阻断牌计算
- 个人 EV
- 团队 EV
- 2 人已知手牌优先支持
- 3-4 人模式逐步开放

### V0.5：模型训练

目标：提高速度和泛化能力。

功能：

- Policy Model
- Value Model
- Belief Model
- Multi-Player Value Model
- Team Policy Model
- Unknown Range Model
- 策略版本评估

### V1.0：产品化策略引擎

目标：稳定支持网站当前牌局采集和策略输出。

功能：

- 鉴权
- 缓存
- 内部批量评估
- 日志和监控
- 策略版本管理
- 回归评估集

## 11. 策略质量评估

每个版本上线前需要评估。

核心指标：

```text
Solver policy KL divergence：模型策略和 Solver 策略差距
EV error：EV 预测误差
Top action accuracy：最高频动作是否一致
Coverage：支持场景覆盖率
Latency：策略响应速度
Stability：同输入结果是否稳定
```

上线门槛示例：

```text
Top action accuracy >= 75%
平均 EV error 控制在可接受范围
策略响应 P95 延迟 <= 3 秒
核心测试集无明显策略反转错误
```

## 12. 风险和应对

### 风险 1：自建策略不够准

应对：

- 第一版明确只覆盖小范围场景。
- 用 Solver 数据校准。
- 建立固定评估集。

### 风险 2：状态空间过大

应对：

- 限定位置、筹码、下注尺度。
- 按高频场景逐步扩展。
- 不追求第一版全覆盖。

### 风险 3：模型学到错误策略

应对：

- 不把普通用户牌局当标准答案。
- 训练数据以 Solver 和人工审核样本为主。
- 每个模型版本必须过评估集。

### 风险 4：策略响应慢

应对：

- 优先查缓存和 Solver 数据库。
- 搜索深度限制在 1-2 层。
- 后期用 Value Model 加速。

### 风险 5：合规和平台风险

应对：

- 产品定位为当前牌局分析、复盘、训练和模拟分析。
- 不提供实时线上牌局自动辅助功能。
- 不鼓励违反第三方平台规则的使用方式。

### 风险 6：多人已知手牌模式复杂度过高

应对：

- 先支持 2 人已知手牌，再扩展 3-4 人。
- 第一版只计算受限动作集合和 1-2 层搜索。
- 明确 objective：actor_ev、team_ev 或 weighted_team_ev。
- 多人模式先以训练研究和内部验证为主，不直接替代普通单人策略。
- 后期用 Multi-Player Value Model 加速团队 EV 估算。

## 13. 第一阶段开发任务清单

建议第一阶段按这个顺序做：

```text
1. 定义牌局输入 JSON schema
2. 实现牌局合法性校验
3. 实现手牌评估和牌面分类
4. 实现 BTN vs BB 默认范围表
5. 实现 Belief 范围更新规则
6. 实现动态动作集合和基础策略树
7. 实现简化 EV 计算
8. 实现 analyze_hand(state)
9. 确认牌局网站可用的采集方式
10. 实现页面状态对象采集或 DOM 采集
11. 实现状态去重 state_hash
12. 实现采集状态到 LBS 引擎的提交流程
13. 接入策略结果展示面板
14. 做 50 个内部固定验证牌局
15. 输出 v0.1 策略评估报告
```

## 14. 推荐第一版目录结构

```text
poker-strategy-engine/
  app/
    main.py
    engine/
      analyze_hand.py
      state.py
      hand_evaluator.py
      board_texture.py
      ranges.py
      belief.py
      strategy_tree.py
      ev.py
      policy.py
      multi_hand.py
      team_ev.py
      known_cards.py
    data/
      default_ranges/
      solver_spots/
    collector/
      state_reader.py
      dom_parser.py
      state_normalizer.py
      state_hash.py
    models/
      policy_model/
      value_model/
      belief_model/
      multi_player_value_model/
      team_policy_model/
      unknown_range_model/
    tests/
      test_analyze_hand.py
      test_ranges.py
      test_ev.py
```

## 15. 开发流程步骤

开发不要直接从模型训练或多人模式开始。建议按“采集闭环 → 单人 LBS-Lite → Solver 数据 → 多人已知手牌 → 模型训练 → 产品化”的顺序推进。

### 15.1 阶段 0：项目初始化

目标：先把工程地基搭好，避免后面边做边乱。

任务：

```text
1. 创建代码仓库
2. 确定 Python 版本和依赖管理方式
3. 建立目录结构
4. 定义 NormalizedState 数据结构
5. 定义 Card / Action / Player / Board / Range 基础类型
6. 建立测试目录
7. 建立策略版本号规则
8. 建立日志和配置文件
```

验收标准：

```text
项目能启动
基础类型能被测试导入
能运行单元测试
能保存一次空的分析日志
```

### 15.2 阶段 1：数据采集闭环

目标：先能从牌局网站读取当前牌局状态。

任务：

```text
1. 判断牌局网站可采集方式：
   - 页面状态对象
   - DOM 元素
   - Hand history / 日志
   - Canvas / OCR
2. 实现 StateReader
3. 实现 DomParser 或 WindowStateReader
4. 实现 StateNormalizer
5. 实现 state_hash 去重
6. 把采集结果输出到调试面板
7. 保存 collected_states 日志
```

验收标准：

```text
能读取 hero_hand
能读取 board
能读取 pot
能读取 action_history
能生成 NormalizedState
同一个局面不会重复触发分析
```

### 15.3 阶段 2：单人 LBS-Lite 引擎

目标：先让一个 Hero 手牌能得到基础策略。

任务：

```text
1. 实现手牌合法性校验
2. 实现牌型识别
3. 实现牌面结构识别
4. 实现默认范围表
5. 实现 Belief 范围更新规则
6. 实现动态动作集合
7. 实现基础策略树
8. 实现简化 EV 计算
9. 实现 analyze_hand(state)
10. 输出 recommend / strategy / ev / confidence
```

验收标准：

```text
支持 BTN vs BB
支持翻牌 Flop
支持无人下注和面对下注两类动作
同一输入结果稳定
50 个内部固定验证牌局能跑完
```

### 15.4 阶段 3：Solver 数据库

目标：让策略从规则估算升级为 Solver 校准。

任务：

```text
1. 设计 solver_spots 表
2. 设计 Solver 导入格式
3. 跑第一批高频场景
4. 标注 board_texture 和 hand_class
5. 实现相似局面检索
6. 实现 Solver 策略和 LBS 策略融合
7. 建立固定评估集
```

验收标准：

```text
能导入 Solver 策略
能按局面查询相似结果
能输出 solver_reference
Top action accuracy 有基础评估数据
```

### 15.5 阶段 4：多人已知手牌研究模式

目标：支持 1-4 个已知手牌，先做训练研究和内部验证。

任务：

```text
1. 扩展 NormalizedState，加入 known_hands
2. 加入 team_seats 和 objective
3. 实现 known_cards.py，从牌库移除已知牌
4. 实现多手牌胜率计算
5. 实现 team_ev.py
6. 先支持 2 人已知手牌
7. 再扩展 3 人和 4 人
8. 多人模式限制搜索深度和动作数量
```

验收标准：

```text
能计算 actor_ev
能计算 team_ev
能输出每个合作方 EV
2 人已知手牌模式稳定
3-4 人模式有明确限制和降级策略
```

### 15.6 阶段 5：模型训练

目标：用数据提升速度和泛化能力。

任务：

```text
1. 整理 Solver 数据和 LBS 搜索数据
2. 训练 Policy Model
3. 训练 Value Model
4. 训练 Belief Model
5. 多人模式训练 Multi-Player Value Model
6. 多人模式训练 Team Policy Model
7. 建立模型版本管理
8. 每个模型上线前跑固定评估集
```

验收标准：

```text
模型输出稳定
模型比纯规则版本更接近 Solver
策略响应速度提升
每个模型版本都有评估报告
```

### 15.7 阶段 6：产品化和长期维护

目标：让策略引擎稳定服务网站使用。

任务：

```text
1. 增加缓存
2. 增加异常状态处理
3. 增加采集失败提示
4. 增加策略版本切换
5. 增加日志监控
6. 增加回归测试
7. 增加策略质量看板
```

验收标准：

```text
策略响应 P95 <= 3 秒
采集失败有明确错误码
策略版本可追踪
线上问题能通过日志复盘
```

## 16. 代码框架规划

代码结构要按职责分层。采集、标准化、策略计算、数据存储、模型训练不要混在一起。

推荐目录：

```text
poker-strategy-engine/
  app/
    main.py
    config.py
    logging_config.py

    collector/
      base.py
      window_state_reader.py
      dom_reader.py
      hand_history_reader.py
      ocr_reader.py
      state_hash.py

    schema/
      cards.py
      actions.py
      players.py
      state.py
      result.py
      ranges.py

    engine/
      analyze_hand.py
      hand_evaluator.py
      equity.py
      board_texture.py
      action_generator.py
      ranges.py
      belief.py
      strategy_tree.py
      ev.py
      policy.py

    multi_hand/
      known_cards.py
      multi_state.py
      team_ev.py
      multi_hand_search.py

    solver/
      importer.py
      spot_matcher.py
      solver_store.py
      solver_types.py

    models/
      policy_model/
      value_model/
      belief_model/
      multi_player_value_model/
      team_policy_model/
      unknown_range_model/

    storage/
      database.py
      repositories/
        collected_states.py
        analysis_logs.py
        solver_spots.py
        model_versions.py

    services/
      analysis_service.py
      collection_service.py
      explanation_service.py
      version_service.py

    ui/
      result_panel/
      debug_panel/

  data/
    default_ranges/
    solver_exports/
    evaluation_sets/

  scripts/
    import_solver_spots.py
    run_evaluation.py
    generate_training_data.py
    train_policy_model.py
    train_value_model.py

  tests/
    unit/
    integration/
    fixtures/
```

### 16.1 分层原则

```text
collector：只负责读取页面或日志，不做策略判断
schema：只定义数据结构，不放业务逻辑
engine：只负责策略计算，不关心页面怎么采集
multi_hand：只放多人已知手牌相关逻辑
solver：只负责 Solver 数据导入、匹配、读取
models：只放模型推理和训练相关代码
storage：只负责数据库读写
services：负责把多个模块串起来
ui：只负责展示结果
```

这样后期如果采集方式变了，不会影响 LBS；如果策略引擎升级，也不会影响采集器。

## 17. 核心代码接口契约

接口契约要提前定好，后面所有模块都围绕这些输入输出开发。

### 17.1 NormalizedState

```python
class NormalizedState:
    mode: str
    table_size: int
    street: str
    current_actor: str
    hero_seat: str | None
    team_seats: list[str]
    known_hands: dict[str, list[str]]
    unknown_seats: list[str]
    board: list[str]
    pot: float
    effective_stacks: dict[str, float]
    action_history: list[dict]
    objective: str
    state_hash: str
```

### 17.2 AnalysisResult

```python
class AnalysisResult:
    recommend: str
    strategy: dict[str, float]
    ev: dict[str, float]
    confidence: float
    reason_codes: list[str]
    engine_version: str
    solver_reference: dict | None
```

多人模式下，`ev` 可以包含：

```text
seat_1
seat_2
team
```

### 17.3 StateReader

```python
class StateReader:
    def read_raw_state(self) -> dict:
        pass
```

职责：

```text
只读取原始页面状态
不做策略判断
不计算 EV
```

### 17.4 StateNormalizer

```python
class StateNormalizer:
    def normalize(self, raw_state: dict) -> NormalizedState:
        pass
```

职责：

```text
把页面采集结果转换成统一牌局状态
校验牌是否合法
生成 state_hash
```

### 17.5 ActionGenerator

```python
class ActionGenerator:
    def legal_actions(self, state: NormalizedState) -> list[str]:
        pass
```

规则：

```text
无人下注：check / bet_33 / bet_75
面对下注：fold / call / raise_3x
V0.2：加入 all_in
后期：根据 SPR 和下注额动态生成
```

### 17.6 BeliefModel

```python
class BeliefModel:
    def estimate_ranges(self, state: NormalizedState) -> dict[str, dict]:
        pass
```

输出：

```text
每个未知玩家的范围概率
```

### 17.7 StrategyEngine

```python
class StrategyEngine:
    def analyze_hand(self, state: NormalizedState) -> AnalysisResult:
        pass
```

这是系统核心入口。采集器、调试工具、内部评估都应该调用这一层，而不是直接调用底层 EV 或策略树模块。

### 17.8 TeamEVCalculator

```python
class TeamEVCalculator:
    def calculate(self, state: NormalizedState, line_result: dict) -> dict[str, float]:
        pass
```

职责：

```text
计算 actor_ev
计算每个 team_seat EV
计算 team_ev
支持 weighted_team_ev
```

## 18. 维护规范

### 18.1 策略版本管理

每次策略变化都要有版本号。

```text
engine_version: lbs-lite-0.1.0
range_version: btn-bb-ranges-0.1.0
solver_dataset_version: solver-spots-0.1.0
model_version: policy-0.1.0
```

分析结果必须记录：

```text
使用了哪个引擎版本
使用了哪个范围版本
是否命中 Solver 数据
是否调用模型
```

### 18.2 测试规范

至少保留四类测试：

```text
unit：单个函数测试
integration：采集到分析的流程测试
regression：固定牌局回归测试
evaluation：策略质量评估
```

重点测试：

```text
牌是否合法
state_hash 是否稳定
动作集合是否合法
EV 是否不会明显反向
多人 known_hands 是否正确从牌库移除
同一输入结果是否稳定
```

### 18.3 错误码规划

建议统一错误码：

```text
INVALID_CARD：牌面非法
DUPLICATE_CARD：重复牌
MISSING_BOARD：公共牌缺失
MISSING_POT：底池缺失
UNKNOWN_POSITION：位置无法识别
UNSUPPORTED_SCENARIO：当前场景暂不支持
COLLECTOR_FAILED：采集失败
STATE_UNCHANGED：状态未变化
LOW_CONFIDENCE：策略置信度低
```

### 18.4 日志规范

每次分析至少记录：

```text
state_hash
normalized_state
legal_actions
recommend
strategy
ev
confidence
engine_version
latency_ms
error_code
```

不要只记录最终推荐动作，否则后期无法复盘策略为什么变化。

### 18.5 扩展规范

新增功能必须按模块扩展：

```text
新增采集方式：加 collector，不改 engine
新增动作尺度：改 action_generator 和 strategy_tree
新增多人模式：改 multi_hand，不污染单人 engine
新增 Solver 数据：改 solver，不改采集器
新增模型：改 models，通过 StrategyEngine 接入
```

## 19. 推荐开发顺序

如果现在开始制作，建议按这个顺序开工：

```text
第 1 周：
搭项目结构、定义 schema、做采集原型。

第 2 周：
做 NormalizedState、state_hash、调试面板。

第 3 周：
做手牌评估、牌面分类、默认范围表。

第 4 周：
做动态动作集合、策略树、简化 EV。

第 5 周：
跑 50 个内部固定验证牌局，修正明显错误。

第 6 周：
接 Solver 数据导入格式，开始小规模校准。

第 7-8 周：
做 2 人已知手牌研究模式。

第 9 周以后：
扩展场景、训练模型、做多人 3-4 人模式。
```

## 20. 最终建议

本项目不要从完整 Solver 或大模型直接开始。

最稳路线是：

```text
自建 LBS-Lite 策略引擎
→ 接 Solver 数据库
→ 扩展更多当前牌局场景
→ 训练模型加速和泛化
→ 做成稳定的网站策略服务
```

策略核心由 LBS / Solver 数据 / 模型负责，大模型只负责解释文字和交互包装。
