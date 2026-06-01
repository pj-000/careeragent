import { defineStore } from "pinia";

import {
  createRun,
  downloadReport,
  getMessages,
  getWorkspace,
  type ArtifactChainItem,
  type ConversationMessage,
  type RunResponse,
  type WorkspaceResponse,
} from "../api/client";

export function makeThreadId(): string {
  return `chat-${Date.now().toString(36)}`;
}

export const quickPrompts = [
  "我会 Python FastAPI，想匹配 Agent 开发岗位",
  "请分析目标岗位 JD：Agent 开发工程师，需要 LangGraph、FastAPI、RAG 和测试能力",
  "请做 match 分析",
  "生成三个月路径规划",
  "根据能力差距给我一个训练任务",
  "我的训练答案：我会设计一个简历解析 Agent，使用 FastAPI 暴露接口，用 LangGraph 编排画像抽取和评分节点。",
  "开始模拟面试",
  "回答1：我会用 StateGraph 定义节点和条件边。",
  "回答2：我会用 thread_id 和 checkpointer 保留会话状态。",
  "回答3：我会把评分结果保存为 Artifact 并进入报告。",
  "请导出 Markdown 报告",
];

export const useWorkbenchStore = defineStore("workbench", {
  state: () => ({
    threadId: makeThreadId(),
    input: "",
    isRunning: false,
    demoMode: new URLSearchParams(window.location.search).get("demo") === "1",
    error: "",
    lastRun: null as RunResponse | null,
    messages: [] as ConversationMessage[],
    workspace: null as WorkspaceResponse | null,
    artifactChain: [] as ArtifactChainItem[],
    reportMarkdown: "",
  }),

  actions: {
    async sendMessage(message?: string) {
      const content = (message ?? this.input).trim();
      if (!content) {
        return;
      }

      this.input = "";
      this.error = "";
      this.isRunning = true;
      try {
        const run = await createRun(this.threadId, content);
        this.lastRun = run;
        this.artifactChain = run.artifact_chain ?? [];
        await this.refreshThread();
      } catch (error) {
        this.error = error instanceof Error ? error.message : "请求失败";
      } finally {
        this.isRunning = false;
      }
    },

    async refreshThread() {
      this.messages = await getMessages(this.threadId);
      this.workspace = await getWorkspace(this.threadId);
      this.artifactChain = this.workspace.artifact_chain;
    },

    resetThread() {
      this.threadId = makeThreadId();
      this.input = "";
      this.isRunning = false;
      this.error = "";
      this.lastRun = null;
      this.messages = [];
      this.workspace = null;
      this.artifactChain = [];
      this.reportMarkdown = "";
    },

    async exportMarkdownReport() {
      this.error = "";
      try {
        this.reportMarkdown = await downloadReport(this.threadId);
        await this.refreshThread();
      } catch (error) {
        this.error = error instanceof Error ? error.message : "报告导出失败";
      }
    },
  },
});
