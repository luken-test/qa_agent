import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

function loadChats() {
  try {
    const saved = localStorage.getItem('qa_chats')
    if (saved) return JSON.parse(saved)
  } catch { /* ignore */ }
  return [{ title: '新对话', messages: [], threadId: 'thread-' + Date.now() }]
}

export const useChatStore = defineStore('chat', () => {
  const chats = ref(loadChats())
  const currentIndex = ref(parseInt(localStorage.getItem('qa_current_chat') || '0'))

  const currentMessages = computed(() => chats.value[currentIndex.value]?.messages || [])
  const currentChat = computed(() => chats.value[currentIndex.value])
  const currentThreadId = computed(() => currentChat.value?.threadId || '')

  function _save() {
    try { localStorage.setItem('qa_chats', JSON.stringify(chats.value)) } catch { /* ignore */ }
    localStorage.setItem('qa_current_chat', String(currentIndex.value))
  }

  function newChat() {
    chats.value.unshift({ title: '新对话', messages: [], threadId: 'thread-' + Date.now() })
    currentIndex.value = 0
    _save()
  }

  function switchChat(i) {
    currentIndex.value = i
    _save()
  }

  function deleteChat(i) {
    if (chats.value.length <= 1) {
      chats.value = [{ title: '新对话', messages: [], threadId: 'thread-' + Date.now() }]
      currentIndex.value = 0
    } else {
      chats.value.splice(i, 1)
      if (currentIndex.value >= chats.value.length) currentIndex.value = chats.value.length - 1
    }
    _save()
  }

  function addMessage(msg) {
    currentChat.value.messages.push(msg)
    _save()
  }

  function updateLastMessage(updater) {
    const msgs = currentChat.value.messages
    if (msgs.length > 0) updater(msgs[msgs.length - 1])
    _save()
  }

  function updateTitle(text) {
    if (currentChat.value.title === '新对话') {
      currentChat.value.title = text.slice(0, 30) + (text.length > 30 ? '...' : '')
      _save()
    }
  }

  return {
    chats, currentIndex, currentMessages, currentChat, currentThreadId,
    newChat, switchChat, deleteChat, addMessage, updateLastMessage, updateTitle,
  }
})
