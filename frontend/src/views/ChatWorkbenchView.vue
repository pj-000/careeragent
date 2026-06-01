<script setup lang="ts">
import { Download, Refresh } from "@element-plus/icons-vue";

import { API_BASE_URL } from "../api/client";
import ConversationPanel from "../components/ConversationPanel.vue";
import RuntimeDrawer from "../components/RuntimeDrawer.vue";
import WorkspaceTabs from "../components/WorkspaceTabs.vue";
import { useWorkbenchStore } from "../stores/workbench";

const workbench = useWorkbenchStore();
</script>

<template>
  <div class="workbench-shell">
    <main class="workspace-main">
      <header class="workbench-header">
        <div class="title-block">
          <span>CareerAgent MVP</span>
          <h1>职业规划工作台</h1>
        </div>

        <div class="header-meta">
          <div class="meta-item">
            <span>线程 ID</span>
            <strong>{{ workbench.threadId }}</strong>
          </div>
          <div class="meta-item">
            <span>接口地址</span>
            <strong>{{ API_BASE_URL }}</strong>
          </div>
        </div>

        <div class="header-actions">
          <el-switch
            v-model="workbench.demoMode"
            inline-prompt
            active-text="演示"
            inactive-text="学生"
            :disabled="workbench.isRunning"
          />
          <el-button
            :icon="Download"
            :loading="workbench.isRunning"
            @click="workbench.exportMarkdownReport()"
          >
            导出报告
          </el-button>
          <el-button
            :icon="Refresh"
            :disabled="workbench.isRunning"
            @click="workbench.resetThread()"
          >
            新线程
          </el-button>
        </div>
      </header>

      <el-alert
        v-if="workbench.error"
        class="error-alert"
        :title="workbench.error"
        type="error"
        show-icon
        :closable="false"
      />

      <section class="content-grid">
        <div class="workspace-area">
          <WorkspaceTabs :workspace="workbench.workspace" />
        </div>
        <RuntimeDrawer
          :last-run="workbench.lastRun"
          :workspace="workbench.workspace"
          :demo-mode="workbench.demoMode"
        />
      </section>
    </main>

    <ConversationPanel
      v-model="workbench.input"
      :messages="workbench.messages"
      :running="workbench.isRunning"
      @send="workbench.sendMessage"
      @reset="workbench.resetThread"
    />
  </div>
</template>

<style scoped>
.workbench-shell {
  display: grid;
  min-height: 100vh;
  grid-template-columns: minmax(0, 1fr) 420px;
  background: #eef2f7;
  color: #172033;
}

.workspace-main {
  display: grid;
  min-width: 0;
  align-content: start;
  gap: 16px;
  padding: 22px;
}

.workbench-header {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(260px, 0.9fr) max-content;
  align-items: center;
  gap: 18px;
  border: 1px solid #d9e1ec;
  border-radius: 8px;
  background: #ffffff;
  padding: 18px 20px;
}

.title-block {
  min-width: 0;
}

.title-block span,
.meta-item span {
  color: #667085;
  font-size: 12px;
}

h1 {
  margin: 3px 0 0;
  color: #111827;
  font-size: 28px;
  line-height: 1.2;
}

.header-meta {
  display: grid;
  min-width: 0;
  gap: 8px;
}

.meta-item {
  display: grid;
  min-width: 0;
  gap: 3px;
}

.meta-item strong {
  min-width: 0;
  overflow: hidden;
  color: #263244;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.error-alert {
  border-radius: 8px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  align-items: start;
  gap: 16px;
}

.workspace-area {
  min-width: 0;
}

@media (max-width: 1100px) {
  .workbench-shell,
  .content-grid,
  .workbench-header {
    grid-template-columns: 1fr;
  }

  .header-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
