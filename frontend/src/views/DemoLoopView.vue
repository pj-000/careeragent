<script setup lang="ts">
import { computed } from "vue";
import {
  Check,
  Download,
  MagicStick,
  Refresh,
  Right,
  VideoPlay,
} from "@element-plus/icons-vue";

import AgentRuntimePanel from "../components/AgentRuntimePanel.vue";
import { API_BASE_URL } from "../api/client";
import { demoSteps, useDemoStore } from "../stores/demo";

const demo = useDemoStore();

const progressPercent = computed(() =>
  Math.round((Math.min(demo.currentStep, demoSteps.length) / demoSteps.length) * 100),
);

const latestKinds = computed(() => new Set(demo.artifacts.map((artifact) => artifact.kind)));

function stepStatus(index: number): "success" | "process" | "wait" {
  if (demo.currentStep > index) {
    return "success";
  }
  if (demo.currentStep === index) {
    return "process";
  }
  return "wait";
}

function hasExpectedArtifact(kinds: string[]): boolean {
  return kinds.some((kind) => latestKinds.value.has(kind));
}
</script>

<template>
  <div class="demo-shell">
    <main class="workspace">
      <section class="topbar">
        <div class="identity">
          <span class="product-name">CareerAgent MVP</span>
          <h1>学生职业闭环 Demo</h1>
        </div>
        <div class="thread-box">
          <span>Thread ID</span>
          <strong>{{ demo.threadId }}</strong>
        </div>
      </section>

      <section class="control-strip">
        <div class="progress-block">
          <div class="progress-copy">
            <strong>{{ demo.currentStep }} / {{ demoSteps.length }}</strong>
            <span>步骤已完成</span>
          </div>
          <el-progress :percentage="progressPercent" :stroke-width="10" />
        </div>

        <div class="actions">
          <el-button
            type="primary"
            :icon="Right"
            :loading="demo.isRunning"
            :disabled="demo.currentStep >= demoSteps.length"
            @click="demo.runNextStep()"
          >
            下一步
          </el-button>
          <el-button
            :icon="VideoPlay"
            :loading="demo.isRunning"
            :disabled="demo.currentStep >= demoSteps.length"
            @click="demo.runFullLoop()"
          >
            连续运行
          </el-button>
          <el-button :icon="Download" :disabled="demo.isRunning" @click="demo.exportMarkdownReport()">
            导出报告
          </el-button>
          <el-button :icon="Refresh" :disabled="demo.isRunning" @click="demo.resetLoop()">
            重置
          </el-button>
        </div>
      </section>

      <el-alert
        v-if="demo.error"
        class="error-alert"
        :title="demo.error"
        type="error"
        show-icon
        :closable="false"
      />

      <section class="student-context">
        <div class="context-card">
          <span>学生画像样例</span>
          <p>Python / FastAPI 基础较好，希望转向 Agent 开发工程师，关注 LangGraph、RAG、测试和后端接口能力。</p>
        </div>
        <div class="context-card">
          <span>目标岗位样例</span>
          <p>Agent 开发工程师：负责多 Agent 编排、业务 API、Artifact 持久化、评估闭环与 Markdown 报告输出。</p>
        </div>
        <div class="context-card">
          <span>API Base</span>
          <p>{{ API_BASE_URL }}</p>
        </div>
      </section>

      <section class="loop-board">
        <article
          v-for="(step, index) in demoSteps"
          :key="step.key"
          class="step-card"
          :class="{ active: demo.currentStep === index, done: demo.currentStep > index }"
        >
          <div class="step-index">
            <el-icon v-if="demo.currentStep > index"><Check /></el-icon>
            <span v-else>{{ index + 1 }}</span>
          </div>

          <div class="step-body">
            <div class="step-heading">
              <div>
                <h2>{{ step.title }}</h2>
                <span>{{ step.agent }}</span>
              </div>
              <el-tag
                :type="hasExpectedArtifact(step.expectedKinds) ? 'success' : 'info'"
                effect="plain"
              >
                {{ step.expectedKinds.join(" / ") }}
              </el-tag>
            </div>
            <p class="description">{{ step.description }}</p>
            <div class="message-box">{{ step.message }}</div>
            <div class="step-actions">
              <el-button
                size="small"
                :type="demo.currentStep === index ? 'primary' : 'default'"
                :icon="MagicStick"
                :loading="demo.runningStep === index"
                :disabled="demo.isRunning"
                @click="demo.runStep(index)"
              >
                调用 /api/runs
              </el-button>
              <el-tag size="small" :type="stepStatus(index)">
                {{ demo.currentStep > index ? "已完成" : demo.currentStep === index ? "当前" : "待运行" }}
              </el-tag>
            </div>
          </div>
        </article>
      </section>

      <section class="history-section">
        <div class="section-title">
          <h2>最近运行</h2>
          <span>{{ demo.runHistory.length }} 条</span>
        </div>
        <el-table v-if="demo.runHistory.length" :data="demo.runHistory.slice(0, 5)" size="small">
          <el-table-column prop="stepTitle" label="步骤" min-width="110" />
          <el-table-column prop="run.active_agent" label="Active Agent" min-width="130" />
          <el-table-column prop="run.run_id" label="Run ID" min-width="170" show-overflow-tooltip />
          <el-table-column label="消息" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ row.message }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="运行后显示最近调用" :image-size="56" />
      </section>
    </main>

    <AgentRuntimePanel
      :last-run="demo.lastRun"
      :artifact-ids="demo.artifactIds"
      :used-skill-refs="demo.usedSkillRefs"
      :running="demo.isRunning"
    />
  </div>
</template>

<style scoped>
.demo-shell {
  display: grid;
  min-height: 100vh;
  grid-template-columns: minmax(0, 1fr) 380px;
  background: #eef2f7;
  color: #162033;
}

.workspace {
  min-width: 0;
  padding: 22px;
}

.topbar,
.control-strip,
.student-context,
.history-section {
  border: 1px solid #d9e0eb;
  border-radius: 8px;
  background: #ffffff;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 20px;
}

.identity {
  min-width: 0;
}

.product-name {
  color: #667085;
  font-size: 13px;
}

h1 {
  margin: 4px 0 0;
  color: #111827;
  font-size: 28px;
  line-height: 1.2;
}

.thread-box {
  display: grid;
  min-width: 220px;
  gap: 4px;
  border-radius: 8px;
  background: #f3f6fb;
  padding: 10px 12px;
}

.thread-box span,
.progress-copy span,
.context-card span,
.step-heading span,
.section-title span {
  color: #667085;
  font-size: 12px;
}

.thread-box strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.control-strip {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) max-content;
  gap: 18px;
  margin-top: 16px;
  padding: 16px 20px;
}

.progress-block {
  min-width: 0;
}

.progress-copy {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.error-alert {
  margin-top: 16px;
}

.student-context {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin-top: 16px;
  overflow: hidden;
}

.context-card {
  min-width: 0;
  background: #ffffff;
  padding: 16px;
}

.context-card p {
  margin: 8px 0 0;
  overflow-wrap: anywhere;
  color: #263244;
  font-size: 14px;
  line-height: 1.55;
}

.loop-board {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.step-card {
  display: grid;
  min-width: 0;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 12px;
  border: 1px solid #d9e0eb;
  border-radius: 8px;
  background: #ffffff;
  padding: 14px;
}

.step-card.active {
  border-color: #409eff;
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.16);
}

.step-card.done {
  background: #fbfdfb;
}

.step-index {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border-radius: 50%;
  background: #e8eef7;
  color: #344054;
  font-weight: 700;
}

.step-card.done .step-index {
  background: #e5f6ee;
  color: #229453;
}

.step-body {
  min-width: 0;
}

.step-heading,
.section-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.step-heading h2,
.section-title h2 {
  margin: 0;
  color: #172033;
  font-size: 17px;
}

.description {
  margin: 9px 0;
  color: #4d596b;
  font-size: 14px;
  line-height: 1.5;
}

.message-box {
  min-height: 44px;
  overflow-wrap: anywhere;
  border-radius: 8px;
  background: #f4f7fb;
  padding: 10px;
  color: #223044;
  font-size: 13px;
  line-height: 1.45;
}

.step-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.history-section {
  margin-top: 16px;
  padding: 16px;
}

.section-title {
  margin-bottom: 12px;
}

@media (max-width: 1180px) {
  .demo-shell {
    grid-template-columns: minmax(0, 1fr) 340px;
  }

  .loop-board,
  .student-context {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 980px) {
  .demo-shell {
    grid-template-columns: 1fr;
  }

  .control-strip {
    grid-template-columns: 1fr;
  }

  .actions {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .workspace {
    padding: 12px;
  }

  .topbar {
    align-items: stretch;
    flex-direction: column;
  }

  .thread-box {
    min-width: 0;
  }

  .step-card {
    grid-template-columns: 30px minmax(0, 1fr);
    padding: 12px;
  }

  .step-index {
    width: 28px;
    height: 28px;
    font-size: 13px;
  }
}
</style>
