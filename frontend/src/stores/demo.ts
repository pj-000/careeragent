import { defineStore } from "pinia";

import { createRun, downloadReport, type ArtifactRef, type RunResponse } from "../api/client";

export interface DemoStep {
  key: string;
  title: string;
  agent: string;
  message: string;
  description: string;
  expectedKinds: string[];
}

export const task8CompleteDemoMessages = [
  "我会 Python FastAPI，想匹配 Agent 开发岗位",
  "请分析目标岗位 JD：Agent 开发工程师，需要 LangGraph、FastAPI、RAG 和测试能力",
  "生成三个月路径规划",
  "根据能力差距给我一个训练任务",
  "我的训练答案：我会设计一个简历解析 Agent，使用 FastAPI 暴露接口，用 LangGraph 编排画像抽取和评分节点。",
  "开始模拟面试",
  "回答1：我会用 StateGraph 定义节点和条件边。",
  "回答2：我会用 thread_id 和 checkpointer 保留会话状态。",
  "回答3：我会把评分结果保存为 Artifact 并进入报告。",
  "请导出 Markdown 报告",
];

export const completeDemoMessages = [
  task8CompleteDemoMessages[0],
  task8CompleteDemoMessages[1],
  "请做 match 分析",
  ...task8CompleteDemoMessages.slice(2),
];

export const demoSteps: DemoStep[] = [
  {
    key: "profile",
    title: "画像输入",
    agent: "profile",
    message: completeDemoMessages[0],
    description: "用学生的技能和职业目标生成结构化画像。",
    expectedKinds: ["profile"],
  },
  {
    key: "job",
    title: "目标岗位 / JD",
    agent: "job",
    message: completeDemoMessages[1],
    description: "拆解 Agent 开发工程师岗位要求。",
    expectedKinds: ["job_analysis"],
  },
  {
    key: "match",
    title: "匹配诊断",
    agent: "match",
    message: completeDemoMessages[2],
    description: "对比画像与岗位，识别能力差距。",
    expectedKinds: ["match"],
  },
  {
    key: "plan",
    title: "路径规划",
    agent: "planning",
    message: completeDemoMessages[3],
    description: "生成三个月职业准备路径。",
    expectedKinds: ["plan"],
  },
  {
    key: "training-task",
    title: "任务训练",
    agent: "training",
    message: completeDemoMessages[4],
    description: "根据差距生成虚拟职场训练任务。",
    expectedKinds: ["training_result"],
  },
  {
    key: "training-answer",
    title: "训练提交",
    agent: "training",
    message: completeDemoMessages[5],
    description: "提交训练答案并获得评分反馈。",
    expectedKinds: ["training_result"],
  },
  {
    key: "interview-start",
    title: "模拟面试",
    agent: "interview",
    message: completeDemoMessages[6],
    description: "启动面试问题与答题节奏。",
    expectedKinds: ["interview_summary"],
  },
  {
    key: "interview-answer-1",
    title: "面试回答 1",
    agent: "interview",
    message: completeDemoMessages[7],
    description: "回答 LangGraph 节点与条件边问题。",
    expectedKinds: ["interview_summary"],
  },
  {
    key: "interview-answer-2",
    title: "面试回答 2",
    agent: "interview",
    message: completeDemoMessages[8],
    description: "回答 thread_id 与 checkpointer 状态保留问题。",
    expectedKinds: ["interview_summary"],
  },
  {
    key: "interview-answer-3",
    title: "面试回答 3",
    agent: "interview",
    message: completeDemoMessages[9],
    description: "回答评分 Artifact 与报告衔接问题。",
    expectedKinds: ["interview_summary"],
  },
  {
    key: "report",
    title: "Markdown 报告",
    agent: "report",
    message: completeDemoMessages[10],
    description: "汇总画像、岗位、匹配、训练和面试产物。",
    expectedKinds: ["report"],
  },
];

interface DemoHistoryItem {
  stepKey: string;
  stepTitle: string;
  message: string;
  run: RunResponse;
}

interface DemoState {
  threadId: string;
  lastRun: RunResponse | null;
  artifactIds: string[];
  artifacts: ArtifactRef[];
  usedSkillRefs: string[];
  currentStep: number;
  runningStep: number | null;
  error: string;
  reportMarkdown: string;
  runHistory: DemoHistoryItem[];
}

function makeThreadId(): string {
  return `demo-${Date.now().toString(36)}`;
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values));
}

export const useDemoStore = defineStore("demo", {
  state: (): DemoState => ({
    threadId: makeThreadId(),
    lastRun: null,
    artifactIds: [],
    artifacts: [],
    usedSkillRefs: [],
    currentStep: 0,
    runningStep: null,
    error: "",
    reportMarkdown: "",
    runHistory: [],
  }),

  getters: {
    isRunning: (state) => state.runningStep !== null,
    completedKinds: (state) => new Set(state.artifacts.map((artifact) => artifact.kind)),
  },

  actions: {
    resetLoop() {
      this.threadId = makeThreadId();
      this.lastRun = null;
      this.artifactIds = [];
      this.artifacts = [];
      this.usedSkillRefs = [];
      this.currentStep = 0;
      this.runningStep = null;
      this.error = "";
      this.reportMarkdown = "";
      this.runHistory = [];
    },

    async runStep(stepIndex: number) {
      const step = demoSteps[stepIndex];
      if (!step) {
        return;
      }

      this.runningStep = stepIndex;
      this.error = "";
      try {
        const run = await createRun(this.threadId, step.message);
        this.lastRun = run;
        this.artifacts = run.artifacts;
        this.artifactIds = run.artifacts.map((artifact) => artifact.id);
        this.usedSkillRefs = unique([...this.usedSkillRefs, ...run.used_skill_refs]);
        this.currentStep = Math.max(this.currentStep, stepIndex + 1);
        this.runHistory.unshift({
          stepKey: step.key,
          stepTitle: step.title,
          message: step.message,
          run,
        });
      } catch (error) {
        this.error = error instanceof Error ? error.message : "请求失败";
      } finally {
        this.runningStep = null;
      }
    },

    async runNextStep() {
      await this.runStep(this.currentStep);
    },

    async runFullLoop() {
      for (let index = this.currentStep; index < demoSteps.length; index += 1) {
        await this.runStep(index);
        if (this.error) {
          break;
        }
      }
    },

    async exportMarkdownReport() {
      this.error = "";
      try {
        this.reportMarkdown = await downloadReport(this.threadId);
        const blob = new Blob([this.reportMarkdown], { type: "text/markdown;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = `careeragent-${this.threadId}.md`;
        anchor.click();
        URL.revokeObjectURL(url);
      } catch (error) {
        this.error = error instanceof Error ? error.message : "报告导出失败";
      }
    },
  },
});
