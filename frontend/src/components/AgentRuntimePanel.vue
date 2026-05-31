<script setup lang="ts">
import { computed } from "vue";
import {
  Cpu,
  Files,
  Connection,
  List,
  Operation,
  Warning,
} from "@element-plus/icons-vue";

import type { RunResponse } from "../api/client";

const props = defineProps<{
  lastRun: RunResponse | null;
  artifactIds: string[];
  usedSkillRefs: string[];
  running: boolean;
}>();

const activeAgent = computed(() => props.lastRun?.active_agent ?? "等待运行");
const warnings = computed(() => props.lastRun?.warnings ?? []);
const artifacts = computed(() => props.lastRun?.artifacts ?? []);
const trace = computed(() => props.lastRun?.agent_trace_summary ?? []);
</script>

<template>
  <aside class="runtime-panel">
    <div class="panel-title">
      <div>
        <span class="eyebrow">Agent Runtime</span>
        <h2>运行态</h2>
      </div>
      <el-tag :type="running ? 'warning' : 'info'" effect="plain">
        {{ running ? "运行中" : "就绪" }}
      </el-tag>
    </div>

    <section class="runtime-section">
      <div class="section-heading">
        <el-icon><Connection /></el-icon>
        <span>Active Agent</span>
      </div>
      <div class="agent-name">{{ activeAgent }}</div>
    </section>

    <section class="runtime-section">
      <div class="section-heading">
        <el-icon><List /></el-icon>
        <span>Used Skills</span>
      </div>
      <div v-if="usedSkillRefs.length" class="tag-list">
        <el-tag
          v-for="skill in usedSkillRefs"
          :key="skill"
          class="runtime-tag"
          effect="plain"
          type="success"
        >
          {{ skill }}
        </el-tag>
      </div>
      <el-empty v-else description="尚未加载 Skill" :image-size="48" />
    </section>

    <section class="runtime-section">
      <div class="section-heading">
        <el-icon><Files /></el-icon>
        <span>Artifacts</span>
      </div>
      <div v-if="artifacts.length" class="artifact-list">
        <div v-for="artifact in artifacts" :key="artifact.id" class="artifact-row">
          <el-tag effect="dark" size="small">{{ artifact.kind }}</el-tag>
          <span>{{ artifact.id }}</span>
        </div>
      </div>
      <div v-else-if="artifactIds.length" class="tag-list">
        <el-tag v-for="artifactId in artifactIds" :key="artifactId" effect="plain">
          {{ artifactId }}
        </el-tag>
      </div>
      <el-empty v-else description="尚无 Artifact" :image-size="48" />
    </section>

    <section class="runtime-section">
      <div class="section-heading">
        <el-icon><Operation /></el-icon>
        <span>Trace</span>
      </div>
      <el-timeline v-if="trace.length" class="trace-list">
        <el-timeline-item
          v-for="item in trace"
          :key="`${item.agent_id}-${item.summary}`"
          :timestamp="item.agent_id"
          placement="top"
        >
          <p>{{ item.summary }}</p>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="等待首次运行" :image-size="48" />
    </section>

    <section class="runtime-section">
      <div class="section-heading">
        <el-icon><Warning /></el-icon>
        <span>Warnings</span>
      </div>
      <div v-if="warnings.length" class="warning-list">
        <el-alert
          v-for="warning in warnings"
          :key="warning"
          :title="warning"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>
      <div v-else class="quiet-line">
        <el-icon><Cpu /></el-icon>
        当前没有告警
      </div>
    </section>
  </aside>
</template>

<style scoped>
.runtime-panel {
  position: sticky;
  top: 20px;
  display: flex;
  max-height: calc(100vh - 40px);
  min-width: 0;
  flex-direction: column;
  gap: 14px;
  overflow: auto;
  border-left: 1px solid #d8dee8;
  background: #f7f9fc;
  padding: 20px;
}

.panel-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.eyebrow {
  color: #6a7280;
  font-size: 12px;
}

h2 {
  margin: 2px 0 0;
  color: #172033;
  font-size: 22px;
}

.runtime-section {
  min-width: 0;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: #ffffff;
  padding: 14px;
}

.section-heading,
.quiet-line {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #586273;
  font-size: 13px;
}

.agent-name {
  margin-top: 10px;
  overflow-wrap: anywhere;
  color: #111827;
  font-size: 24px;
  font-weight: 700;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.runtime-tag {
  max-width: 100%;
}

.artifact-list,
.warning-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.artifact-row {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  color: #263244;
  font-size: 13px;
}

.artifact-row span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trace-list {
  margin-top: 12px;
  padding-left: 4px;
}

.trace-list p {
  margin: 0;
  overflow-wrap: anywhere;
  color: #2f3a4c;
  font-size: 13px;
}

@media (max-width: 980px) {
  .runtime-panel {
    position: static;
    max-height: none;
    border-left: 0;
    border-top: 1px solid #d8dee8;
  }
}
</style>
