<template>
  <div class="sidebar" :class="{ open: modelValue }">
    <div class="sidebar-header">
      <span class="sidebar-header-title">对话记录</span>
      <button class="sidebar-close" @click="$emit('update:modelValue', false)">&times;</button>
    </div>
    <button class="sidebar-new" @click="chatStore.newChat(); $emit('update:modelValue', false)">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      新建对话
    </button>
    <div class="sidebar-list">
      <div v-for="(chat, i) in chatStore.chats" :key="i"
        class="sidebar-item" :class="{ active: chatStore.currentIndex === i }"
        @click="chatStore.switchChat(i); $emit('update:modelValue', false)">
        <span class="sidebar-item-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
        </span>
        <span class="sidebar-item-title">{{ chat.title }}</span>
        <span class="sidebar-item-delete" @click.stop="chatStore.deleteChat(i)">&times;</span>
      </div>
    </div>
  </div>
  <div v-if="modelValue" class="sidebar-mask" @click="$emit('update:modelValue', false)"></div>
</template>

<script setup>
import { useChatStore } from '../stores/chat'

defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])

const chatStore = useChatStore()
</script>
