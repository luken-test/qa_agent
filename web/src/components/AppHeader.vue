<template>
  <header class="header">
    <div class="header-left">
      <button class="icon-btn" @click="$emit('toggleSidebar')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
      </button>
      <div class="logo-area">
        <div class="logo-icon">
          <svg width="18" height="18" viewBox="0 0 120 120" fill="none">
            <path d="M60 22 L88 36 L88 64 Q88 82 60 98 Q32 82 32 64 L32 36 Z" stroke="#fff" stroke-width="5" stroke-linejoin="round" fill="none"/>
            <polyline points="46,58 56,70 76,48" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="logo">QA Agent</span>
      </div>
    </div>
    <div class="header-right">
      <div class="model-picker" @click="showMenu = !showMenu" ref="pickerRef">
        <span class="model-label">{{ modelStore.currentLabel }}</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2.5"><polyline points="6,9 12,15 18,9"/></svg>
        <div v-if="showMenu" class="model-menu">
          <div class="menu-group">
            <div class="menu-group-title">智谱 GLM</div>
            <div v-for="m in modelStore.zhipuModels" :key="m.value" class="menu-item" :class="{ active: modelStore.selected === m.value }" @click.stop="modelStore.select(m.value); showMenu = false">
              <span>{{ m.label }}</span>
              <span v-if="m.tag" class="menu-tag">{{ m.tag }}</span>
            </div>
          </div>
          <div class="menu-divider"></div>
          <div class="menu-group">
            <div class="menu-group-title">Claude</div>
            <div v-for="m in modelStore.claudeModels" :key="m.value" class="menu-item" :class="{ active: modelStore.selected === m.value }" @click.stop="modelStore.select(m.value); showMenu = false">
              <span>{{ m.label }}</span>
            </div>
          </div>
          <div class="menu-divider"></div>
          <div class="menu-group">
            <div class="menu-group-title">OpenAI</div>
            <div v-for="m in modelStore.openaiModels" :key="m.value" class="menu-item" :class="{ active: modelStore.selected === m.value }" @click.stop="modelStore.select(m.value); showMenu = false">
              <span>{{ m.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useModelStore } from '../stores/model'

defineEmits(['toggleSidebar'])

const modelStore = useModelStore()
const showMenu = ref(false)
const pickerRef = ref(null)

onMounted(() => {
  document.addEventListener('click', (e) => {
    if (pickerRef.value && !pickerRef.value.contains(e.target)) showMenu.value = false
  })
})
</script>
