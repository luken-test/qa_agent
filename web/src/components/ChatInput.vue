<template>
  <div class="input-wrapper">
    <div class="input-container">
      <div class="type-picker">
        <button v-for="t in types" :key="t.value" class="type-btn" :class="{ active: taskType === t.value }" @click="setTaskType(t.value)">
          <span v-html="t.icon"></span>
          <span>{{ t.label }}</span>
        </button>
      </div>
      <div class="input-box">
        <textarea
          ref="inputRef"
          v-model="inputText"
          @keydown.enter.exact="send($event)"
          @input="autoResize"
          :placeholder="typePlaceholder"
          rows="1"
        ></textarea>
        <button class="send-btn" @click="send()" :disabled="!taskType || !inputText.trim() || sending">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5,12 12,5 19,12"/>
          </svg>
        </button>
      </div>
      <p class="input-hint">{{ taskType ? 'Enter 发送，Shift+Enter 换行' : '请先选择任务类型' }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChat } from '../composables/useChat'

const { inputText, sending, taskType, typePlaceholder, send, setTaskType, quickInput } = useChat()
const inputRef = ref(null)

function autoResize() {
  const ta = inputRef.value
  if (!ta) return
  ta.style.height = 'auto'
  ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
}

defineExpose({ inputRef, quickInput })

const types = [
  { value: 'qa', label: 'IT知识问答', icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>' },
  { value: 'testcase', label: '测试用例', icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>' },
  { value: 'jmeter', label: 'JMeter', icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>' },
  { value: 'bug', label: 'Bug 报告', icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>' }
]
</script>
