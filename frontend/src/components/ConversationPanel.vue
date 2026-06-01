<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { Promotion as Send, RefreshLeft as RotateCcw } from "@element-plus/icons-vue";

import type { ConversationMessage } from "../api/client";
import { quickPrompts } from "../stores/workbench";

const props = defineProps<{
  messages: ConversationMessage[];
  running: boolean;
}>();

const input = defineModel<string>({ required: true });

const emit = defineEmits<{
  send: [message?: string];
  reset: [];
}>();

const messageList = ref<HTMLElement | null>(null);

const visibleMessages = computed(() =>
  props.messages.filter((message) => message.role === "user" || message.role === "assistant"),
);

function speakerLabel(role: ConversationMessage["role"]): string {
  return role === "user" ? "你" : "CareerAgent";
}

function sendCurrentMessage() {
  const content = input.value.trim();
  if (!content || props.running) {
    return;
  }
  emit("send");
}

function sendQuickPrompt(prompt: string) {
  if (props.running) {
    return;
  }
  emit("send", prompt);
}

watch(
  () => visibleMessages.value.length,
  async () => {
    await nextTick();
    if (messageList.value) {
      messageList.value.scrollTop = messageList.value.scrollHeight;
    }
  },
);
</script>

<template>
  <aside class="conversation-panel">
    <header class="conversation-header">
      <div>
        <span>CareerAgent</span>
        <h2>对话助手</h2>
      </div>
      <el-tooltip content="新线程" placement="left">
        <el-button
          circle
          :icon="RotateCcw"
          :disabled="running"
          aria-label="新线程"
          @click="emit('reset')"
        />
      </el-tooltip>
    </header>

    <div class="quick-prompts">
      <el-tag
        v-for="prompt in quickPrompts"
        :key="prompt"
        class="quick-prompt"
        effect="plain"
        round
        @click="sendQuickPrompt(prompt)"
      >
        {{ prompt }}
      </el-tag>
    </div>

    <div ref="messageList" class="message-list">
      <template v-if="visibleMessages.length">
        <article
          v-for="message in visibleMessages"
          :key="message.id"
          class="message-row"
          :class="message.role"
        >
          <div class="message-meta">{{ speakerLabel(message.role) }}</div>
          <div class="message-bubble">{{ message.content }}</div>
        </article>
      </template>
      <el-empty v-else description="还没有对话，直接描述你的目标或粘贴岗位 JD" :image-size="64" />
    </div>

    <footer class="composer">
      <el-input
        v-model="input"
        type="textarea"
        :autosize="{ minRows: 3, maxRows: 6 }"
        resize="none"
        maxlength="3000"
        show-word-limit
        placeholder="输入你的职业目标、岗位 JD、训练答案或面试回答"
        :disabled="running"
        @keydown.enter.exact.prevent="sendCurrentMessage"
      />
      <el-button
        type="primary"
        :icon="Send"
        :loading="running"
        :disabled="!input.trim()"
        @click="sendCurrentMessage"
      >
        发送
      </el-button>
    </footer>
  </aside>
</template>

<style scoped>
.conversation-panel {
  display: flex;
  min-width: 0;
  height: 100vh;
  flex-direction: column;
  border-left: 1px solid #d6dde8;
  background: #fbfcfe;
}

.conversation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid #e1e6ef;
  padding: 18px;
}

.conversation-header span {
  color: #657084;
  font-size: 12px;
}

.conversation-header h2 {
  margin: 2px 0 0;
  color: #172033;
  font-size: 20px;
  line-height: 1.2;
}

.quick-prompts {
  display: flex;
  max-height: 122px;
  flex-wrap: wrap;
  gap: 8px;
  overflow: auto;
  border-bottom: 1px solid #e1e6ef;
  padding: 14px 18px;
}

.quick-prompt {
  max-width: 100%;
  cursor: pointer;
}

.message-list {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  gap: 14px;
  overflow: auto;
  padding: 18px;
}

.message-row {
  display: grid;
  max-width: 92%;
  gap: 6px;
}

.message-row.user {
  align-self: flex-end;
}

.message-row.assistant {
  align-self: flex-start;
}

.message-meta {
  color: #667085;
  font-size: 12px;
}

.message-row.user .message-meta {
  text-align: right;
}

.message-bubble {
  border: 1px solid #dce3ed;
  border-radius: 8px;
  background: #ffffff;
  padding: 10px 12px;
  color: #172033;
  font-size: 14px;
  line-height: 1.55;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

.message-row.user .message-bubble {
  border-color: #2f6fed;
  background: #2f6fed;
  color: #ffffff;
}

.composer {
  display: grid;
  gap: 10px;
  border-top: 1px solid #e1e6ef;
  padding: 14px 18px 18px;
}

.composer .el-button {
  width: 100%;
}

@media (max-width: 1100px) {
  .conversation-panel {
    height: auto;
    min-height: 560px;
    border-left: 0;
    border-top: 1px solid #d6dde8;
  }
}
</style>
