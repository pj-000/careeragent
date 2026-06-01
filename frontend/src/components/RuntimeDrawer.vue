<script setup lang="ts">
import { computed } from "vue";
import { Cpu, Files, Guide as Route, List as ListChecks, Warning } from "@element-plus/icons-vue";

import type { RunResponse, WorkspaceResponse } from "../api/client";

const props = defineProps<{
  lastRun: RunResponse | null;
  workspace: WorkspaceResponse | null;
  demoMode: boolean;
}>();

const statusRows = computed(() => [
  { label: "运行状态", value: props.lastRun?.run_status ?? "等待运行" },
  { label: "业务 Agent", value: props.lastRun?.last_business_agent ?? "暂无" },
  { label: "运行节点", value: props.lastRun?.current_runtime_node ?? "暂无" },
]);

const missingCapabilities = computed(() => {
  const direct = props.lastRun?.missing_capabilities ?? [];
  const decision = props.lastRun?.supervisor_decision?.missing_capabilities ?? [];
  return Array.from(new Set([...direct, ...decision]));
});

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
</script>

<template>
  <aside class="runtime-drawer">
    <header class="drawer-header">
      <div>
        <span>运行时</span>
        <h2>运行状态</h2>
      </div>
      <el-tag :type="lastRun?.run_status === 'completed' ? 'success' : 'info'" effect="plain">
        {{ demoMode ? "演示模式" : "学生模式" }}
      </el-tag>
    </header>

    <section class="runtime-section">
      <div class="section-title">
        <el-icon><Cpu /></el-icon>
        <span>当前状态</span>
      </div>
      <dl class="status-list">
        <template v-for="row in statusRows" :key="row.label">
          <dt>{{ row.label }}</dt>
          <dd>{{ row.value }}</dd>
        </template>
      </dl>
      <div class="capabilities">
        <span>缺失能力</span>
        <div v-if="missingCapabilities.length" class="tag-list">
          <el-tag v-for="item in missingCapabilities" :key="item" type="warning" effect="plain">
            {{ item }}
          </el-tag>
        </div>
        <p v-else>暂无</p>
      </div>
    </section>

    <template v-if="demoMode">
      <section class="runtime-section">
        <div class="section-title">
          <el-icon><ListChecks /></el-icon>
          <span>技能加载</span>
        </div>
        <pre v-if="lastRun?.used_skill_runtime_refs.length">{{ formatJson(lastRun.used_skill_runtime_refs) }}</pre>
        <el-empty v-else description="尚未加载技能引用" :image-size="48" />
      </section>

      <section class="runtime-section">
        <div class="section-title">
          <el-icon><Route /></el-icon>
          <span>Artifact 关系</span>
        </div>
        <div v-if="workspace?.artifact_chain.length" class="artifact-chain">
          <div v-for="item in workspace.artifact_chain" :key="item.id" class="artifact-row">
            <div>
              <el-tag size="small" effect="plain">{{ item.kind }}</el-tag>
              <strong>{{ item.id }}</strong>
            </div>
            <span>父级：{{ item.parent_artifact_ids.length ? item.parent_artifact_ids.join(" / ") : "无" }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无 Artifact 关系" :image-size="48" />
      </section>

      <section class="runtime-section">
        <div class="section-title">
          <el-icon><Files /></el-icon>
          <span>上下文压缩快照</span>
        </div>
        <pre v-if="lastRun?.compaction_snapshot">{{ formatJson(lastRun.compaction_snapshot) }}</pre>
        <el-empty v-else description="暂无压缩快照" :image-size="48" />
      </section>

      <section class="runtime-section">
        <div class="section-title">
          <el-icon><Files /></el-icon>
          <span>记忆更新</span>
        </div>
        <pre v-if="lastRun?.memory_updates.length">{{ formatJson(lastRun.memory_updates) }}</pre>
        <el-empty v-else description="暂无记忆更新" :image-size="48" />
      </section>

      <section class="runtime-section">
        <div class="section-title">
          <el-icon><Warning /></el-icon>
          <span>告警</span>
        </div>
        <div v-if="lastRun?.warnings.length" class="warning-list">
          <el-alert
            v-for="warning in lastRun.warnings"
            :key="warning"
            :title="warning"
            type="warning"
            :closable="false"
            show-icon
          />
        </div>
        <el-empty v-else description="暂无告警" :image-size="48" />
      </section>
    </template>
  </aside>
</template>

<style scoped>
.runtime-drawer {
  display: grid;
  gap: 14px;
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.drawer-header span,
.capabilities span {
  color: #667085;
  font-size: 12px;
}

.drawer-header h2 {
  margin: 2px 0 0;
  color: #172033;
  font-size: 20px;
}

.runtime-section {
  min-width: 0;
  border: 1px solid #d9e1ec;
  border-radius: 8px;
  background: #ffffff;
  padding: 14px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #344054;
  font-size: 13px;
  font-weight: 700;
}

.status-list {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: 10px 14px;
  margin: 14px 0 0;
}

.status-list dt {
  color: #667085;
  font-size: 12px;
}

.status-list dd {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
  color: #172033;
  font-size: 13px;
  font-weight: 700;
}

.capabilities {
  margin-top: 16px;
}

.capabilities p {
  margin: 8px 0 0;
  color: #344054;
  font-size: 13px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.artifact-chain,
.warning-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.artifact-row {
  display: grid;
  gap: 6px;
  border-top: 1px solid #eef2f7;
  padding-top: 10px;
}

.artifact-row:first-child {
  border-top: 0;
  padding-top: 0;
}

.artifact-row div {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  align-items: center;
  gap: 8px;
}

.artifact-row strong,
.artifact-row span {
  overflow-wrap: anywhere;
  color: #344054;
  font-size: 12px;
}

pre {
  max-height: 260px;
  margin: 12px 0 0;
  overflow: auto;
  border: 1px solid #e1e7f0;
  border-radius: 8px;
  background: #101828;
  padding: 12px;
  color: #e6edf7;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
