# CareerAgent MVP 设计文档

日期：2026-05-30

## 目标

CareerAgent 是一个面向高校学生个人使用的职业发展智能体系统。MVP 目标是做出一条完整、可本地演示的个人职业规划闭环：建立职业画像、选择或自定义目标岗位、完成人岗匹配、生成发展路径、进行虚拟职场任务训练、完成文字模拟面试，并导出个人职业发展报告。

原始申报书提出的是“面向高校大学生高质量就业的职业发展数字孪生与智能规划系统”。本设计将该申报目标收敛为一个可实现、可演示、后续可扩展的 MVP。

## 产品范围

第一版是学生个人职业规划工具，不是教师管理平台，也不是就业管理后台。

纳入 MVP：

- 学生上传简历、粘贴简历文本、手动编辑职业画像。
- 构建学生职业数字孪生，包括技能、经历、偏好、目标和能力证据链。
- 支持预置岗位，也支持学生输入自定义目标岗位或 JD。
- 主线演示岗位为 Agent 开发工程师 / AI Agent Developer。
- 输出人岗匹配分、优势、短板和可解释证据。
- 生成个性化职业发展路径。
- 支持画像、匹配、规划、训练、面试、报告等场景化多轮对话。
- 使用 LangGraph 实现严格多 Agent 架构。
- 支持短期记忆、长期记忆和上下文压缩。
- 支持虚拟职场任务生成、学生提交、AI 评分和反馈。
- 支持文字为主的模拟面试、追问和评分。
- 支持 Markdown 个人职业发展报告导出。
- 本地优先运行，结构上预留 Docker 或服务器部署空间。

MVP 暂不做：

- 教师端、班级管理、学生列表。
- 账号体系和权限系统。
- 生产级数据库。
- 复杂后台管理。
- 必须可用的语音或视频面试分析。
- 生产部署流水线。
- 完整 PDF 导出；第一版先做 Markdown 导出。

## 已确认关键决策

- 后端：Python FastAPI。
- 前端：Vue 3、Vite、TypeScript、Element Plus。
- 多 Agent 编排：LangGraph。
- 数据存储：JSON 文件。
- 模型接入：真实调用 qwen3.6-plus 和 deepseek-v4-flash。
- 模型行为：关键推理节点在模型支持时启用思考模式。
- 用户定位：一个学生个人用户，附带两个演示学生样例。
- 岗位定位：预置岗位 + 自定义岗位/JD 分析。
- 报告导出：Markdown 优先，PDF 后续扩展。

## 演示学生样例

MVP 内置两个学生样例：

- 计算机专业学生，目标岗位为 Agent 开发工程师。用于展示“接近目标岗位时的能力提升路径”。
- 非计算机专业转 AI 的学生，目标岗位为 Agent 开发工程师。用于展示“跨专业转型时的差距诊断和转型路线”。

## 系统架构

系统采用分层架构：

1. Vue 学生端
   - 负责学生工作流和交互体验。
   - 展示结构化结果、图表、表单、训练任务、面试对话和报告。
   - 页面右侧保留当前场景的智能体对话栏。

2. FastAPI 应用层
   - 负责 HTTP API、文件上传、会话创建、报告导出和 JSON 持久化。
   - 前端调用业务 API，后端内部再调用 LangGraph 工作流。

3. LangGraph 多 Agent 运行时
   - 负责图状态、Agent 路由、条件跳转、checkpoint 和 handoff。
   - LangGraph 不是 Agent 本身，而是承载多 Agent 协作的编排骨架。

4. Agent 层
   - 每个 Agent 是相对独立的业务智能主体。
   - 每个 Agent 都有目标、工具、私有上下文、记忆范围、输入输出协议和交接策略。

5. Memory 层
   - 区分短期对话/任务记忆和长期学生职业数字孪生记忆。
   - 对长对话执行上下文压缩。

6. Model Provider 层
   - 将 Qwen 和 DeepSeek 封装在统一模型调用接口后面。
   - Agent 不直接感知具体 API 细节。

## 严格多 Agent 设计

本系统将“多 Agent”定义为一种架构范式，而不是固定流水线的别名。LangGraph 用来实现这种架构范式。

每个 Agent 都必须具备：

- 独立目标和成功标准。
- 与自身职责匹配的工具集合。
- 私有短期上下文。
- 有范围限制的长期记忆访问权限。
- 结构化输入输出协议。
- handoff 策略：什么时候追问学生、调用其他 Agent、交还给 Supervisor 或结束任务。

Agent 团队：

- Supervisor Agent
  - 理解学生意图。
  - 决定下一步调用哪个 Agent 或子图。
  - 判断任务是否完成，或是否需要澄清。

- Memory Manager Agent
  - 检索相关短期和长期记忆。
  - 对长对话进行摘要和压缩。
  - 判断哪些信息可以写入长期记忆。

- Profile Agent
  - 解析简历和表单。
  - 创建或更新学生职业数字孪生。
  - 发现缺失信息并向学生追问。

- Job Agent
  - 分析预置岗位或自定义岗位/JD。
  - 生成岗位能力画像，包括职责、工具、技能、评价维度和岗位期望。

- Match Agent
  - 比较学生画像和岗位画像。
  - 输出匹配分、优势、短板、证据和优先提升项。

- Planning Agent
  - 生成阶段化职业发展路径。
  - 根据“三个月”等时间约束调整计划。
  - 输出学习任务、项目建议和里程碑。

- Training Agent
  - 生成虚拟职场任务。
  - 按评分标准评价学生提交。
  - 输出改进建议和下一轮训练建议。

- Interview Agent
  - 进行文字模拟面试。
  - 根据学生回答继续追问。
  - 输出评分、表达问题和技术短板总结。

- Report Agent
  - 整合画像、匹配、规划、训练和面试结果。
  - 生成 Markdown 个人职业发展报告。

协作示例：

当学生问“我只有三个月，能不能转 Agent 开发？”时，Supervisor Agent 会判断需要读取画像、分析岗位、诊断差距和生成路径，然后依次或按需协调 Profile Agent、Job Agent、Match Agent、Planning Agent 和 Report Agent。如果画像证据不足，Profile Agent 可以先追问学生，而不是直接生成结论。

## 记忆设计

系统有两层记忆。

短期记忆：

- 当前对话线程。
- 当前页面或模块上下文。
- 当前训练提交和修改历史。
- 当前模拟面试问题和追问历史。
- 未确认推断和临时工作信息。

短期记忆通过 LangGraph state/checkpoint 和 JSON conversation 文件管理。

长期记忆：

- 已确认个人事实。
- 教育背景。
- 技能与能力证据。
- 项目、实习、竞赛和课程经历。
- 职业目标和偏好。
- 历史训练得分与反馈。
- 面试短板和成长轨迹。

长期记忆存储为 JSON 文件，后续可以迁移到数据库。

长期记忆写入规则：

- 学生明确填写的信息和简历中的明确事实，可以带来源写入。
- 模型推断必须带置信度，必要时要求学生确认。
- 低置信度猜测、一次性闲聊、失败草稿、模型隐藏思考过程不写入长期记忆。
- 每条长期记忆包含 `source`、`confidence`、`updated_at`、`confirmed_by_user` 和必要的 `evidence`。

## 上下文压缩设计

长对话使用类似 Claude Code 和 Codex 这类编码 Agent 的 compaction 思路。目标不是生成普通聊天摘要，而是保存可恢复的任务状态。

压缩触发：

- 上下文接近阈值时自动预警。
- 上下文达到更高阈值时自动压缩。
- 学生手动点击“整理上下文”。
- 模块切换，例如画像进入匹配、面试进入报告。
- 任务完成，例如训练评分完成或面试结束。

压缩产物为结构化 `CompactionSnapshot`：

- `goal_summary`：当前学生目标、目标岗位和时间约束。
- `confirmed_facts`：已确认学生事实、证据和置信度。
- `decisions`：重要选择及其原因。
- `module_state`：当前页面、相关对象 ID 和未完成任务。
- `agent_notes`：各 Agent 可复用结论，不保存完整思考链。
- `open_questions`：缺失信息和阻塞点。
- `next_actions`：建议下一步和可能调用的 Agent。
- `source_index`：来源消息范围和对象 ID。

多 Agent 压缩策略：

- 每个 Agent 维护自己的 `AgentSnapshot`。
- Supervisor Agent 读取 `GlobalSnapshot` 来继续路由。
- Memory Manager 判断哪些 snapshot 内容可以写入长期记忆。
- 下一次模型调用输入为：最近 N 轮原文 + 相关 snapshot + 相关长期记忆。
- 不持久化模型完整 thinking 内容，只保存可复用结论和依据摘要。

## 前端设计

前端使用 Vue 3、Vite、TypeScript、Element Plus、Vue Router、Pinia、lucide-vue-next，并可选 ECharts。

主页面：

- `DashboardView`：首页总览，展示当前目标岗位、匹配分、主要短板和下一步建议。
- `ProfileView`：职业画像，支持简历上传/粘贴、手动编辑、能力证据链查看。
- `JobMatchView`：岗位匹配，支持预置岗位、自定义岗位/JD、岗位画像、匹配结果和差距解释。
- `PlanView`：路径规划，展示阶段路线、学习任务、项目建议和里程碑。
- `TrainingView`：虚拟职场任务舱，展示任务、答案编辑器、评分反馈和修改闭环。
- `InterviewView`：模拟面试，展示文字问答、追问和评分总结。
- `ReportView`：个人报告，支持 Markdown 预览和导出。

关键组件：

- `AppShell`：整体布局和左侧导航。
- `AgentChatPanel`：右侧场景化多轮对话栏。
- `ResumeUploader`：简历上传和文本粘贴。
- `ProfileEditor`：结构化画像表单。
- `SkillEvidenceList`：能力证据链。
- `JobSelector`：预置岗位选择。
- `CustomJobForm`：自定义岗位/JD 输入。
- `MatchRadar`：能力匹配图。
- `GapAnalysisCard`：能力差距说明。
- `PlanTimeline`：阶段化路径。
- `TrainingTaskCard`：训练任务和评分展示。
- `InterviewThread`：面试消息和追问。
- `MarkdownReport`：报告预览和导出。

布局：

- 左侧：导航。
- 中间：当前页面的结构化工作区。
- 右侧：当前场景 Agent 对话栏。

右侧对话栏随页面切换上下文。例如，在岗位匹配页它服务于 Match Agent，在面试页它服务于 Interview Agent。

## 后端设计

FastAPI 后端模块结构：

```text
backend/
  app/
    main.py
    api/
    schemas/
    repositories/
    agents/
    graphs/
    memory/
    providers/
    services/
```

模块职责：

- `api/`：HTTP 接口。
- `schemas/`：Pydantic 请求和响应模型。
- `repositories/`：JSON 文件读写。
- `agents/`：Agent 提示词、工具和协议。
- `graphs/`：LangGraph supervisor、子图和工作流。
- `memory/`：短期记忆、长期记忆和上下文压缩。
- `providers/`：Qwen 和 DeepSeek API 封装。
- `services/`：简历解析、报告导出、文件处理和业务编排辅助逻辑。

主要 API：

- `POST /api/profiles/parse-resume`：上传或粘贴简历内容，生成画像草稿。
- `GET /api/profiles/{profile_id}`：获取学生画像。
- `PATCH /api/profiles/{profile_id}`：编辑学生画像。
- `POST /api/jobs/analyze`：分析预置岗位或自定义岗位/JD。
- `POST /api/matches`：生成匹配诊断。
- `POST /api/plans`：生成职业路径规划。
- `POST /api/training/tasks`：生成虚拟职场任务。
- `POST /api/training/submissions`：提交答案并获得评分反馈。
- `POST /api/interviews/sessions`：开始模拟面试。
- `POST /api/interviews/{session_id}/messages`：继续面试对话。
- `POST /api/conversations/{scope}/messages`：发送场景化多轮对话消息。
- `POST /api/reports`：生成报告。
- `GET /api/reports/{report_id}/markdown`：导出 Markdown 报告。

前端只调用业务 API，不直接调用某个具体 Agent。

## 数据文件结构

目录结构：

```text
data/
  demo/
    students.json
    jobs.json
    training_tasks.json
  runtime/
    profiles/
      <profile_id>.json
    jobs/
      <job_id>.json
    matches/
      <match_id>.json
    plans/
      <plan_id>.json
    conversations/
      <conversation_id>.json
    training/
      <submission_id>.json
    interviews/
      <session_id>.json
    reports/
      <report_id>.md
```

核心对象：

- `StudentProfile`：个人信息、教育经历、技能、经历、偏好、目标和证据链。
- `JobProfile`：岗位名称、职责、能力要求、工具、评价维度和来源 JD。
- `MatchResult`：匹配分、优势、短板、证据和提升优先级。
- `CareerPlan`：阶段、学习任务、项目任务、时间安排和里程碑。
- `TrainingSubmission`：任务、学生答案、评分维度、反馈和下一步建议。
- `InterviewSession`：问题、回答、追问、评分和最终总结。
- `ConversationSession`：场景、消息、短期状态、关联对象和压缩快照。
- `LongTermMemory`：已确认事实、职业偏好、技能证据、成长历史和记忆元数据。

## 模型 Provider 设计

Agent 通过模型路由器调用模型，不直接访问具体 provider API。

```python
class ModelProvider:
    async def generate(self, messages, schema=None, thinking=True, model=None):
        ...
```

Provider：

- `QwenProvider`
- `DeepSeekProvider`

默认分工：

- Qwen：画像抽取、自然语言报告、路径说明、面向学生的表达整理。
- DeepSeek：岗位分析、匹配诊断、复核、面试追问、评分和第二意见。
- Qwen + DeepSeek：重要规划和报告路径可采用一个模型生成、另一个模型复核。

结构化输出使用 Pydantic schema 校验。若模型输出不符合 schema，后端执行一次格式修复调用；仍失败则返回结构化错误。

## 错误处理

- 模型 API 失败：
  - 保留用户输入。
  - 前端显示可重试错误。
  - 后端记录 provider、model、请求场景和错误元数据。

- 模型输出不合规：
  - 按 schema 校验。
  - 执行一次格式修复重试。
  - 修复失败后返回结构化错误。

- 简历解析失败：
  - 返回空画像或部分画像。
  - 让学生手动补充缺失字段。

- JSON 写入失败：
  - 不覆盖旧文件。
  - 返回保存失败提示。

- 上下文过长：
  - 运行 Context Manager 压缩。
  - 使用最近原文、snapshot 和相关长期记忆继续对话。

- 长期记忆冲突：
  - 保留原已确认事实。
  - 将新内容标记为未确认，或让学生选择以哪个为准。

## 测试策略

后端测试：

- Pydantic schema 校验。
- JSON Repository 读写行为。
- ModelProvider mock 响应。
- LangGraph 节点输入输出协议。
- Supervisor 常见意图路由。
- Memory Manager 长期记忆写入规则。
- Context compaction snapshot 结构。
- 训练评分流程。
- 面试多轮流程。
- 报告生成流程。

前端测试：

- Demo 数据可加载。
- 简历上传/粘贴流程能生成画像草稿。
- 手动画像编辑能保存。
- 预置岗位和自定义岗位都能分析。
- 匹配结果能展示分数、短板和证据。
- 任务提交后能展示评分反馈。
- 面试多轮消息能持续显示上下文。
- Markdown 报告能生成和下载。

人工验收：

- 本地启动后端和前端。
- 用两个演示学生完整走通主流程。
- 测试一个自定义岗位/JD。
- 至少在三个模块触发多轮对话。
- 导出 Markdown 报告。

## MVP 验收标准

MVP 完成时，本地用户应能：

1. 选择演示学生，或通过上传/粘贴简历创建画像。
2. 查看并编辑职业数字孪生。
3. 选择 Agent 开发岗位，或输入自定义岗位/JD。
4. 生成岗位画像。
5. 生成匹配分、优势、短板和能力证据链。
6. 生成阶段化职业发展路径。
7. 完成一次虚拟职场任务提交并获得 AI 评分反馈。
8. 完成一次文字模拟面试，包含追问和总结评分。
9. 在画像、匹配、规划、训练、面试和报告场景下进行多轮对话。
10. 将短期对话和长期职业数字孪生记忆保存到 JSON 文件。
11. 触发上下文压缩，并能基于压缩快照继续对话。
12. 生成并导出 Markdown 个人职业发展报告。

## 风险与应对

- LLM API 不稳定：
  - 返回可重试错误，保留用户输入。

- 模型输出漂移：
  - 使用结构化 schema 和一次格式修复。

- 记忆污染：
  - 区分短期记忆、长期记忆和压缩快照。
  - 长期事实必须带来源、置信度和确认状态。

- 范围膨胀：
  - 教师端、账号、数据库、语音/视频分析不进入 MVP。

- 前端复杂度：
  - 使用 Element Plus 和少量稳定复用组件。

- 框架复杂度：
  - 先实现小型 LangGraph supervisor 和少量 Agent 子图。
  - 主演示闭环跑通后，再增加高级 handoff 行为。

## 建议实现顺序

1. 搭建项目骨架：FastAPI 后端、Vue 前端、统一开发脚本。
2. 实现 JSON Repository 和 Pydantic schemas。
3. 实现 ModelProvider 和 mock provider 测试。
4. 准备两个演示学生和预置岗位数据。
5. 实现职业画像流程。
6. 实现岗位分析和匹配诊断。
7. 实现路径规划。
8. 实现场景化对话栏和短期记忆。
9. 实现任务生成和评分。
10. 实现模拟面试。
11. 实现长期记忆和上下文压缩快照。
12. 实现 Markdown 报告生成。
13. 完整演示验证和界面打磨。

## 设计状态

本设计已覆盖当前确认的产品决策：

- 学生个人使用，不做教师端。
- FastAPI + Vue。
- JSON 文件存储。
- LangGraph 严格多 Agent 架构。
- 短期记忆和长期职业数字孪生记忆。
- 参考编码 Agent 的上下文压缩机制。
- 真实接入 Qwen 和 DeepSeek。
- Markdown 报告优先，PDF 后续扩展。

