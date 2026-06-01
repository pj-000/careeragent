<script setup lang="ts">
import { computed, ref } from "vue";

import type { WorkspaceResponse } from "../api/client";

const props = defineProps<{
  workspace: WorkspaceResponse | null;
}>();

const tabs = [
  { key: "overview", label: "总览" },
  { key: "profile", label: "画像" },
  { key: "job_analysis", label: "岗位" },
  { key: "match", label: "匹配" },
  { key: "plan", label: "规划" },
  { key: "training_result", label: "训练" },
  { key: "interview_summary", label: "面试" },
  { key: "report", label: "报告" },
] as const;

const activeTab = ref("overview");

const artifactCount = computed(() => props.workspace?.artifact_chain.length ?? 0);

function artifactFor(kind: string): Record<string, unknown> | null {
  return props.workspace?.workspace_artifacts[kind] ?? null;
}

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
</script>

<template>
  <section class="workspace-tabs">
    <el-tabs v-model="activeTab">
      <el-tab-pane v-for="tab in tabs" :key="tab.key" :label="tab.label" :name="tab.key">
        <div v-if="tab.key === 'overview'" class="overview-pane">
          <div class="metric-panel">
            <span>当前目标</span>
            <strong>{{ workspace?.active_context.active_goal || "尚未形成目标" }}</strong>
          </div>
          <div class="metric-panel">
            <span>Artifact 链</span>
            <strong>{{ artifactCount }} 个</strong>
          </div>
          <div class="chain-panel">
            <h3>活跃链路</h3>
            <div v-if="workspace?.artifact_chain.length" class="chain-list">
              <div v-for="item in workspace.artifact_chain" :key="item.id" class="chain-item">
                <el-tag effect="plain">{{ item.kind }}</el-tag>
                <span>{{ item.id }}</span>
              </div>
            </div>
            <el-empty v-else description="暂无活跃 Artifact" :image-size="56" />
          </div>
        </div>

        <div v-else class="artifact-pane">
          <pre v-if="artifactFor(tab.key)">{{ formatJson(artifactFor(tab.key)) }}</pre>
          <el-empty v-else :description="`${tab.label}内容尚未生成`" :image-size="64" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </section>
</template>

<style scoped>
.workspace-tabs {
  min-width: 0;
  border: 1px solid #d9e1ec;
  border-radius: 8px;
  background: #ffffff;
  padding: 8px 16px 16px;
}

.overview-pane {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.metric-panel,
.chain-panel {
  min-width: 0;
  border: 1px solid #e1e7f0;
  border-radius: 8px;
  background: #fbfcff;
  padding: 14px;
}

.metric-panel span {
  display: block;
  color: #667085;
  font-size: 12px;
}

.metric-panel strong {
  display: block;
  margin-top: 8px;
  overflow-wrap: anywhere;
  color: #172033;
  font-size: 18px;
}

.chain-panel {
  grid-column: 1 / -1;
}

.chain-panel h3 {
  margin: 0 0 12px;
  color: #243043;
  font-size: 15px;
}

.chain-list {
  display: grid;
  gap: 8px;
}

.chain-item {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  color: #344054;
  font-size: 13px;
}

.chain-item span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.artifact-pane {
  min-height: 360px;
}

pre {
  max-height: 58vh;
  margin: 0;
  overflow: auto;
  border: 1px solid #e1e7f0;
  border-radius: 8px;
  background: #101828;
  padding: 14px;
  color: #e6edf7;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

@media (max-width: 720px) {
  .overview-pane {
    grid-template-columns: 1fr;
  }
}
</style>
