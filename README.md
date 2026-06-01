# CareerAgent MVP

CareerAgent MVP 是一个本地优先的学生职业发展多 Agent demo。它用一个中文 Chat Workbench 帮助学生从简历/背景出发，通过自然对话完成目标岗位理解、能力匹配、学习规划、训练任务、文字面试和 Markdown 报告导出。

这个版本面向演示和架构验证：默认可以使用 mock 模型模式在本地跑通流程；如需接入真实模型，可通过环境变量配置 Qwen 或 DeepSeek。

## 核心架构

- **FastAPI**：后端 API 入口，负责运行 Agent workflow、读取/写入本地 JSON artifact，并提供报告导出等接口。
- **Vue 3**：前端 Chat Workbench，包含右侧多轮对话、结构化 Workspace Tabs、学生模式/演示模式 Runtime Drawer 和报告导出体验。
- **LangGraph strict multi-agent**：使用 LangGraph `StateGraph` 和 `thread_id` 驱动严格多 Agent 编排，保留 handoff trace、Agent 权限边界和可恢复线程上下文。
- **JSON artifacts**：画像、岗位、匹配、规划、训练、面试、压缩快照和报告都以结构化 JSON artifact 落盘，便于调试、复现和演示。
- **Skills**：不同 Agent 按任务加载对应 Skill，例如简历解析、Agent 开发岗位分析、匹配评分、三个月规划、训练评分、面试流程和 Markdown 报告。
- **Memory / Compaction**：通过 Memory Manager 和 CompactionSnapshot 保存关键上下文，降低长对话恢复成本。
- **Provider DTO**：模型调用通过 provider-neutral DTO 抽象，支持 mock、Qwen、DeepSeek 等 provider 适配。

## 本地数据

运行时学生数据存放在：

```text
data/runtime/
```

该目录用于保存本地 JSON artifacts、线程产物和演示数据，已经被 `.gitignore` 忽略。请不要把真实学生数据提交到仓库。

## 后端启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

后端默认监听 `http://localhost:8000`。

## 前端启动

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器通常会显示一个 Vite 本地地址，例如 `http://localhost:5173`。

## 环境变量

复制 `.env.example` 后按需填写：

```bash
cp .env.example .env
```

默认 `CAREERAGENT_MODEL_MODE=mock`，适合本地演示。接入真实模型时，填写对应 API key、base URL 和模型名，并在后端启动前加载环境变量。

## 演示主线

1. 打开前端工作台，页面会直接进入“职业规划工作台”。
2. 在右侧对话栏输入学生背景，例如“我会 Python FastAPI，想匹配 Agent 开发岗位”。
3. 继续输入自定义 JD，请求匹配、三个月规划和训练任务。
4. 在提交训练答案前尝试开始面试，确认系统会阻塞并提示先完成训练评分。
5. 提交训练答案后完成三轮文字面试。
6. 切换演示模式，查看业务 Agent、运行节点、Skill refs、Artifact 链、记忆更新和上下文压缩快照。
7. 导出 Markdown 职业发展报告。
8. 重启后端，用同一个 `thread_id` 重新读取消息、Workspace 和 JSON artifacts，验证本地可恢复。

## 常用接口

- `POST /api/runs`：统一触发 LangGraph 多 Agent runtime。
- `GET /api/threads/{thread_id}/workspace`：读取当前 active workspace context、活跃 artifacts 和 artifact chain。
- `GET /api/threads/{thread_id}/messages`：读取同一线程的持久化对话消息。
- `POST /api/profiles/demo`：写入演示画像 artifact。
- `POST /api/jobs/demo`：写入演示岗位 artifact。
- `POST /api/training`：训练任务流程入口。
- `POST /api/interviews`：文字面试流程入口。
- `GET /api/reports/{thread_id}/markdown`：导出 Markdown 报告。
