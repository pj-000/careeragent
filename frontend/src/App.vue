<script setup lang="ts">
import ChatWorkbenchView from "./views/ChatWorkbenchView.vue";
</script>

<template>
  <ChatWorkbenchView />
</template>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family:
    Inter,
    "PingFang SC",
    "Microsoft YaHei",
    Arial,
    sans-serif;
}

button,
input,
textarea {
  font: inherit;
}

.el-button span {
  min-width: 0;
}

.el-tag__content {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
