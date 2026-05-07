import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const ALL_MODELS = [
  { value: 'zhipu:glm-4-flash', label: 'GLM-4-Flash', tag: '免费' },
  { value: 'zhipu:glm-4-air', label: 'GLM-4-Air' },
  { value: 'zhipu:glm-4-airx', label: 'GLM-4-AirX' },
  { value: 'zhipu:glm-4-long', label: 'GLM-4-Long' },
  { value: 'zhipu:glm-4-plus', label: 'GLM-4-Plus' },
  { value: 'zhipu:glm-4', label: 'GLM-4' },
  { value: 'claude:claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
  { value: 'claude:claude-opus-4-7', label: 'Claude Opus 4.7' },
  { value: 'openai:gpt-4o', label: 'GPT-4o' },
  { value: 'openai:gpt-4o-mini', label: 'GPT-4o-mini' },
]

export const useModelStore = defineStore('model', () => {
  const selected = ref(localStorage.getItem('qa_model') || 'zhipu:glm-4-flash')

  const zhipuModels = ALL_MODELS.filter(m => m.value.startsWith('zhipu'))
  const claudeModels = ALL_MODELS.filter(m => m.value.startsWith('claude'))
  const openaiModels = ALL_MODELS.filter(m => m.value.startsWith('openai'))
  const currentLabel = computed(() => ALL_MODELS.find(m => m.value === selected.value)?.label || 'GLM-4-Flash')

  function select(val) {
    selected.value = val
    localStorage.setItem('qa_model', val)
  }

  return { selected, zhipuModels, claudeModels, openaiModels, currentLabel, select }
})
