# CareerAgent MVP 5 分钟演示脚本

## 0:00 - 0:30 开场

大家好，今天演示的是 CareerAgent MVP，一个本地优先的学生职业发展多 Agent demo。它不是单次问答工具，而是围绕一个学生的职业发展线程，把简历分析、目标岗位匹配、学习规划、训练、面试和报告沉淀串成一条可恢复的闭环。

演示会使用本地 mock 模型模式，重点看多 Agent runtime、Skill refs、JSON artifacts 和同一 `thread_id` 的恢复能力。

## 0:30 - 1:00 选择样例或粘贴简历

进入前端页面后，先选择样例学生；如果需要展示自定义输入，也可以直接粘贴一段学生简历。这里使用样例学生，背景是有 Python / FastAPI 基础，希望转向 Agent 开发工程师。

此时后端会把学生画像写成结构化 artifact，后续 Agent 不依赖前端临时状态，而是围绕同一个 `thread_id` 读取和追加产物。

## 1:00 - 1:30 选择目标岗位：Agent 开发工程师

接着选择目标岗位：Agent 开发工程师。这个岗位关注多 Agent 编排、后端 API、Artifact 持久化、测试、评估闭环和报告输出。

Job Agent 会加载岗位分析相关 Skill，特别是 Agent 开发岗位参考能力项，然后把岗位要求也保存成 JSON artifact。

## 1:30 - 2:10 Match Agent：匹配、Skill refs、Artifact

点击运行匹配流程。这里可以观察右侧 runtime 面板：当前 Agent 会从 Supervisor handoff 到 Match Agent，再把结果交给后续节点。

重点展示三件事：

- Match Agent 生成学生与 Agent 开发工程师岗位的匹配评分和差距诊断。
- 面板中出现本轮使用过的 Skill refs，例如匹配评分 rubric、差距诊断、岗位能力参考。
- Artifacts 列表新增 match 相关产物，说明结果已经落到本地 JSON，而不是只存在一次性聊天记录里。

## 2:10 - 2:45 Planning：生成学习计划

进入 Planning 阶段。Planning Agent 会基于学生画像、目标岗位和匹配差距，生成阶段性学习路径。

演示时强调：计划不是泛泛建议，而是引用前面 artifacts 的结构化结果，例如后端接口能力、LangGraph 编排、测试意识和项目作品沉淀。Planning 结果也会写入 plan artifact，供训练和报告继续复用。

## 2:45 - 3:20 训练提交

进入训练任务。Training Agent 会给出一个贴近 Agent 开发工程师岗位的任务，例如设计一个小型 Agent workflow、补充 API 契约或描述测试方案。

提交一段训练答案后，系统返回反馈：指出亮点、缺口和下一步改进。这里展示训练提交也会生成 training artifact，并与前面的 profile、job、match、plan artifacts 形成链路。

## 3:20 - 4:10 三轮文字面试

进入文字面试。Interview Agent 按三轮推进，每轮围绕 Agent 开发工程师能力提问。

第一轮可以问项目经历和 LangGraph 编排理解；第二轮追问状态管理、thread_id 或 Artifact 设计；第三轮评估测试、上线风险或协作表达。每轮回答后，系统保存面试过程和阶段反馈。

演示时说明：三轮面试不是简单生成三道题，而是同一线程中的渐进式对话，会读取已有画像、岗位、计划和训练表现。

## 4:10 - 4:35 Markdown 导出

点击导出 Markdown 报告。Report Agent 会汇总学生画像、岗位目标、匹配结果、学习计划、训练反馈和面试总结，生成一份可复制、可归档的职业发展报告。

这里展示报告正文，并说明 Markdown 是从 JSON artifacts 组合出来的，因此能追溯每一段结论来自哪个阶段产物。

## 4:35 - 5:00 重启恢复验证

最后做恢复验证：停止并重启后端服务，然后继续使用同一个 `thread_id` 查询或导出报告。

因为 runtime student data 存在 `data/runtime/`，并且每个阶段都写入 JSON artifact，重启后系统仍能读取同一线程的画像、岗位、匹配、计划、训练、面试和报告数据。这一步证明 CareerAgent MVP 是本地优先、artifact-first、可恢复的多 Agent demo。

## 演示结束语

这就是 CareerAgent MVP 的核心价值：前端看到的是学生职业发展闭环，后端证明的是 FastAPI、Vue 3、LangGraph strict multi-agent、Skills、Memory / Compaction、Provider DTO 和本地 JSON artifacts 的完整协作。

## v3.1 Chat Workbench 演示路径

1. 打开前端工作台，确认页面直接进入职业规划工作区，而不是营销页。
2. 在右侧对话栏输入：“我会 Python FastAPI，想匹配 Agent 开发岗位。”
3. 观察中间画像 tab 出现 profile artifact，演示模式下 Runtime Drawer 显示业务 Agent 和最终 `memory_manager` 节点。
4. 继续输入自定义 JD，请求匹配、规划、训练任务、训练答案、三轮面试和报告。
5. 在只有训练任务、尚未提交训练答案时尝试开始面试，确认系统提示需要先提交训练答案并完成评分。
6. 切换到演示模式，展示 active artifact chain、parent relationships、used skills、compaction snapshot。
7. 导出 Markdown 报告，说明报告读取 active workspace context，不混用同线程其他目标岗位的历史 artifact。
