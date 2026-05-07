<template>
  <div class="welcome">
    <div class="welcome-icon">
      <svg width="36" height="36" viewBox="0 0 120 120" fill="none">
        <path d="M60 22 L88 36 L88 64 Q88 82 60 98 Q32 82 32 64 L32 36 Z" stroke="#fff" stroke-width="5" stroke-linejoin="round" fill="none"/>
        <polyline points="46,58 56,70 76,48" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <h1 class="welcome-title">你好，我是 QA Agent</h1>
    <p class="welcome-sub">你的 AI 测试工程师助手，专注于互联网 IT 领域的测试能力</p>
    <div class="feature-grid">
      <div v-for="f in features" :key="f.type" class="feature-card" @click="$emit('quickInput', f.type)">
        <div class="feature-icon" :class="f.iconClass" v-html="f.icon"></div>
        <div class="feature-info">
          <div class="feature-name">{{ f.name }}</div>
          <div class="feature-desc">{{ f.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['quickInput'])

const features = [
  {
    type: 'testcase', name: '生成测试用例', desc: '从需求描述自动生成结构化测试用例',
    iconClass: 'feature-icon--blue',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10,9 9,9 8,9"/></svg>',
  },
  {
    type: 'jmeter', name: 'Curl 转 JMeter', desc: '一键将 curl 命令转为 JMeter 脚本',
    iconClass: 'feature-icon--orange',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
  },
  {
    type: 'bug', name: '生成 Bug 报告', desc: '根据缺陷描述生成规范 Bug 单',
    iconClass: 'feature-icon--red',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
  },
  {
    type: 'qa', name: '测试知识问答', desc: '互联网 IT 测试知识智能问答',
    iconClass: 'feature-icon--green',
    icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  },
]
</script>
