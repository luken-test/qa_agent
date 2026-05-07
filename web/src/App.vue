<template>
  <div class="chat-app">
    <ChatSidebar v-model="showSidebar" />

    <div class="chat-body">
      <AppHeader @toggle-sidebar="showSidebar = true" />

      <main class="main">
        <WelcomePage v-if="chatStore.currentMessages.length === 0" @quick-input="handleQuickInput" />
        <div v-else class="messages" ref="messagesRef">
          <MessageItem v-for="(msg, i) in chatStore.currentMessages" :key="i" :msg="msg" />
        </div>
      </main>

      <ChatInput ref="chatInputRef" />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from './stores/chat'
import ChatSidebar from './components/ChatSidebar.vue'
import AppHeader from './components/AppHeader.vue'
import WelcomePage from './components/WelcomePage.vue'
import MessageItem from './components/MessageItem.vue'
import ChatInput from './components/ChatInput.vue'

const chatStore = useChatStore()
const showSidebar = ref(false)
const messagesRef = ref(null)
const chatInputRef = ref(null)

function scrollToBottom() {
  nextTick(() => { if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight })
}

watch(() => chatStore.currentMessages.length, () => scrollToBottom())
watch(() => {
  const msgs = chatStore.currentMessages
  return msgs.length > 0 ? msgs[msgs.length - 1] : null
}, () => scrollToBottom(), { deep: true })

function handleQuickInput(type) {
  chatInputRef.value?.quickInput(type)
  chatInputRef.value?.inputRef?.focus()
}
</script>

<style>
:root {
  --bg: #f5f5f7;
  --surface: #ffffff;
  --surface-hover: #f0f0f2;
  --border: #e5e5ea;
  --border-light: #f0f0f2;
  --text: #1d1d1f;
  --text-secondary: #6e6e73;
  --text-muted: #aeaeb2;
  --blue: #007aff;
  --blue-bg: #eff6ff;
  --orange: #ff9500;
  --orange-bg: #fff8f0;
  --red: #ff3b30;
  --red-bg: #fff5f5;
  --green: #34c759;
  --green-bg: #f2faf5;
  --radius: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow: 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
  --shadow-lg: 0 12px 40px rgba(0,0,0,0.08);
  --transition: 0.2s ease;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif; color: var(--text); background: var(--bg); -webkit-font-smoothing: antialiased; }

.chat-app { display: flex; height: 100vh; position: relative; }
.chat-body { display: flex; flex-direction: column; flex: 1; min-width: 0; background: var(--bg); }

/* ========== 侧边栏 ========== */
.sidebar {
  position: fixed; left: 0; top: 0; bottom: 0; width: 300px;
  background: var(--surface); border-right: 1px solid var(--border);
  transform: translateX(-100%); transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 200; display: flex; flex-direction: column;
  box-shadow: var(--shadow-lg);
}
.sidebar.open { transform: translateX(0); }
.sidebar-header {
  padding: 20px 24px; display: flex; justify-content: space-between;
  align-items: center; border-bottom: 1px solid var(--border-light);
}
.sidebar-header-title { font-size: 15px; font-weight: 600; color: var(--text); }
.sidebar-close { background: none; border: none; font-size: 22px; cursor: pointer; color: var(--text-muted); padding: 4px 8px; border-radius: 8px; transition: var(--transition); }
.sidebar-close:hover { color: var(--text); background: var(--surface-hover); }
.sidebar-new {
  margin: 16px; padding: 12px; border: 1.5px dashed var(--border); border-radius: var(--radius);
  background: var(--surface); cursor: pointer; font-size: 13px; color: var(--text-secondary);
  display: flex; align-items: center; gap: 8px; justify-content: center;
  transition: var(--transition); font-weight: 500;
}
.sidebar-new:hover { background: var(--surface-hover); border-color: var(--text-muted); color: var(--text); }
.sidebar-list { flex: 1; overflow-y: auto; padding: 8px; }
.sidebar-item {
  padding: 12px 14px; border-radius: 10px; cursor: pointer;
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: var(--text-secondary); margin-bottom: 2px;
  transition: var(--transition);
}
.sidebar-item:hover { background: var(--surface-hover); }
.sidebar-item.active { background: var(--text); color: #fff; }
.sidebar-item.active .sidebar-item-icon svg { stroke: #fff; }
.sidebar-item-icon { flex-shrink: 0; display: flex; opacity: 0.5; }
.sidebar-item.active .sidebar-item-icon { opacity: 1; }
.sidebar-item-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; font-weight: 450; }
.sidebar-item-delete { opacity: 0; color: var(--text-muted); cursor: pointer; font-size: 16px; padding: 0 4px; transition: var(--transition); }
.sidebar-item:hover .sidebar-item-delete { opacity: 1; }
.sidebar-item.active .sidebar-item-delete { color: rgba(255,255,255,0.6); }
.sidebar-item-delete:hover { color: var(--text) !important; }
.sidebar-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.2); z-index: 199; backdrop-filter: blur(4px); }

/* ========== 顶部栏 ========== */
.header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 24px; height: 60px; background: var(--surface);
  border-bottom: 1px solid var(--border-light); flex-shrink: 0;
}
.header-left { display: flex; align-items: center; gap: 14px; }
.header-right { display: flex; align-items: center; }
.icon-btn {
  width: 38px; height: 38px; border: none; border-radius: 10px;
  background: transparent; cursor: pointer; display: flex;
  align-items: center; justify-content: center; transition: var(--transition);
}
.icon-btn:hover { background: var(--surface-hover); }
.logo-area { display: flex; align-items: center; gap: 10px; }
.logo-icon {
  width: 30px; height: 30px; border-radius: 8px; background: var(--text);
  display: flex; align-items: center; justify-content: center;
}
.logo { font-size: 17px; font-weight: 700; color: var(--text); letter-spacing: -0.3px; }

/* 模型选择器 */
.model-picker {
  position: relative; display: flex; align-items: center; gap: 6px;
  padding: 7px 16px; border: 1px solid var(--border); border-radius: 24px;
  background: var(--surface); cursor: pointer; font-size: 13px; color: var(--text-secondary);
  transition: var(--transition); user-select: none;
}
.model-picker:hover { background: var(--surface-hover); border-color: var(--border); }
.model-label { font-size: 13px; font-weight: 500; }
.model-menu {
  position: absolute; top: calc(100% + 8px); right: 0;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow-lg); min-width: 210px; padding: 6px; z-index: 100;
}
.menu-group-title { font-size: 11px; color: var(--text-muted); font-weight: 600; padding: 10px 12px 6px; letter-spacing: 0.3px; }
.menu-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 12px; border-radius: 8px; font-size: 13px; color: var(--text);
  cursor: pointer; transition: var(--transition);
}
.menu-item:hover { background: var(--bg); }
.menu-item.active { color: var(--text); background: var(--surface-hover); font-weight: 600; }
.menu-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 10px;
  background: var(--green-bg); color: var(--green); font-weight: 600;
}
.menu-divider { height: 1px; background: var(--border-light); margin: 4px 8px; }

/* ========== 主内容区 ========== */
.main { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }

/* ========== 欢迎页 ========== */
.welcome {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 40px 24px; text-align: center;
}
.welcome-icon {
  width: 64px; height: 64px; border-radius: 18px; background: var(--text);
  display: flex; align-items: center; justify-content: center; margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.welcome-title { font-size: 26px; font-weight: 700; color: var(--text); margin-bottom: 10px; letter-spacing: -0.5px; }
.welcome-sub { font-size: 15px; color: var(--text-muted); margin-bottom: 40px; max-width: 400px; line-height: 1.5; }

.feature-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
  max-width: 520px; width: 100%;
}
.feature-card {
  display: flex; align-items: flex-start; gap: 14px;
  padding: 18px 20px; border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--surface); cursor: pointer; text-align: left;
  transition: all 0.25s ease;
}
.feature-card:hover { border-color: #c7c7cc; box-shadow: var(--shadow-md); transform: translateY(-2px); }
.feature-icon {
  width: 40px; height: 40px; border-radius: 10px; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0;
}
.feature-icon--blue { background: var(--blue-bg); color: var(--blue); }
.feature-icon--orange { background: var(--orange-bg); color: var(--orange); }
.feature-icon--red { background: var(--red-bg); color: var(--red); }
.feature-icon--green { background: var(--green-bg); color: var(--green); }
.feature-name { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 3px; }
.feature-desc { font-size: 12px; color: var(--text-muted); line-height: 1.4; }

/* ========== 消息列表 ========== */
.messages { max-width: 780px; width: 100%; margin: 0 auto; padding: 28px 24px; }
.messages > .msg-row { margin-bottom: 24px; }

/* 消息行 */
.msg-row { display: flex; gap: 12px; max-width: 88%; }
.msg-row--user { margin-left: auto; flex-direction: row; justify-content: flex-end; }
.msg-row--ai { margin-right: auto; }

/* 头像 */
.msg-avatar {
  width: 32px; height: 32px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  margin-top: 2px;
}
.msg-avatar--user { background: var(--surface-hover); color: var(--text-secondary); }
.msg-avatar--ai { background: var(--text); }

/* 消息内容 */
.msg-content { line-height: 1.6; font-size: 14px; }
.msg-content--user {
  background: var(--text); color: #fff; padding: 10px 18px;
  border-radius: 18px 18px 4px 18px; white-space: pre-wrap; word-break: break-word;
  font-weight: 450;
}
.msg-content--ai {
  background: var(--surface); padding: 20px 24px; border-radius: 4px 18px 18px 18px;
  border: 1px solid var(--border-light); box-shadow: var(--shadow-sm);
  width: 100%;
}

/* ========== Markdown 渲染 ========== */
.md-body { line-height: 1.8; color: var(--text); font-size: 14px; }
.md-body > *:first-child { margin-top: 0; }
.md-body > *:last-child { margin-bottom: 0; }
.md-body p { margin: 0 0 12px; }
.md-body h1 { font-size: 20px; font-weight: 700; color: var(--text); margin: 20px 0 10px; padding-bottom: 8px; border-bottom: 2px solid var(--border-light); }
.md-body h2 { font-size: 17px; font-weight: 700; color: var(--text); margin: 18px 0 8px; padding-bottom: 6px; border-bottom: 1px solid var(--border-light); }
.md-body h3 { font-size: 15px; font-weight: 600; color: var(--text); margin: 14px 0 6px; }
.md-body h4, .md-body h5, .md-body h6 { font-size: 14px; font-weight: 600; color: var(--text); margin: 12px 0 6px; }
.md-body ul, .md-body ol { padding-left: 24px; margin: 8px 0; }
.md-body ul { list-style-type: disc; }
.md-body ol { list-style-type: decimal; }
.md-body li { margin: 4px 0; line-height: 1.7; }
.md-body li > ul, .md-body li > ol { margin: 4px 0; }
.md-body strong { font-weight: 600; color: var(--text); }
.md-body em { font-style: italic; }
.md-body a { color: var(--text-secondary); text-decoration: none; border-bottom: 1px solid transparent; transition: var(--transition); }
.md-body a:hover { border-bottom-color: var(--text-secondary); }

.md-body code {
  background: var(--bg); color: var(--text); padding: 2px 7px;
  border-radius: 5px; font-size: 13px; font-family: 'SF Mono', 'Cascadia Code', Consolas, 'Courier New', monospace;
}

.md-body pre {
  background: #1e1e2e; color: #cdd6f4; padding: 0; border-radius: 10px;
  overflow: hidden; margin: 12px 0; font-size: 13px;
}
.md-body pre code {
  display: block; padding: 16px 20px; overflow-x: auto;
  background: none; color: inherit; font-size: 13px;
  font-family: 'SF Mono', 'Cascadia Code', Consolas, 'Courier New', monospace;
  line-height: 1.6; border-radius: 0;
}

.md-body blockquote {
  border-left: 3px solid var(--text-muted); background: var(--bg);
  padding: 10px 16px; margin: 12px 0; border-radius: 0 8px 8px 0;
  color: var(--text-secondary); font-size: 13.5px;
}
.md-body blockquote p { margin-bottom: 4px; }

.md-body table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; border-radius: 8px; overflow: hidden; }
.md-body thead th { background: var(--surface-hover); font-weight: 600; color: var(--text); text-align: left; padding: 10px 14px; border-bottom: 2px solid var(--border); }
.md-body tbody td { padding: 10px 14px; border-bottom: 1px solid var(--border-light); }
.md-body tbody tr:hover { background: var(--surface-hover); }
.md-body tbody tr:last-child td { border-bottom: none; }

.md-body hr { border: none; height: 1px; background: var(--border); margin: 16px 0; }

/* ========== 加载动画 ========== */
.loading-indicator { display: flex; align-items: center; gap: 10px; padding: 4px 0; }
.loading-pulse {
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--text-muted); opacity: 0.6;
  animation: pulse-ring 1.5s ease-in-out infinite;
}
@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 0.6; }
  50% { transform: scale(1.1); opacity: 0.3; }
  100% { transform: scale(0.8); opacity: 0.6; }
}
.loading-text { font-size: 13px; color: var(--text-muted); font-weight: 450; }

/* ========== 错误提示 ========== */
.msg-error {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  background: var(--red-bg); color: var(--red); border-radius: 10px;
  font-size: 13px; border: 1px solid rgba(255,59,48,0.15);
}

/* ========== 结果卡片 ========== */
.result-card {
  margin-top: 16px; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 20px; box-shadow: var(--shadow-sm);
}
.result-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.result-tag {
  display: inline-flex; align-items: center; padding: 4px 14px; border-radius: 20px;
  font-size: 12px; font-weight: 600; color: #fff;
}
.result-tag--jmeter { background: var(--orange); }
.result-tag--testcase { background: var(--blue); }
.result-tag--bug { background: var(--red); }
.result-tag--execute { background: var(--green); }
.action-btn--green { background: var(--green); color: #fff; border-color: var(--green); }
.action-btn--green:hover { background: #2db84d; border-color: #2db84d; }
.result-name { font-size: 13px; color: var(--text-muted); }

.result-stats {
  display: flex; gap: 0; margin-bottom: 16px;
  background: var(--bg); border-radius: 10px; overflow: hidden;
  border: 1px solid var(--border-light);
}
.stat-item {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  padding: 12px 16px; border-right: 1px solid var(--border-light);
}
.stat-item:last-child { border-right: none; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--text); }
.stat-label { font-size: 11px; color: var(--text-muted); margin-top: 2px; font-weight: 500; }

.code-details { margin-bottom: 12px; }
.code-details summary {
  cursor: pointer; color: var(--text-secondary); font-size: 13px;
  padding: 8px 0; font-weight: 500; transition: var(--transition); user-select: none;
}
.code-details summary:hover { color: var(--text); }
.code-block {
  background: #1e1e2e; color: #cdd6f4; padding: 16px 20px; border-radius: 10px;
  overflow-x: auto; max-height: 300px; font-size: 12px; line-height: 1.6;
  font-family: 'SF Mono', 'Cascadia Code', Consolas, 'Courier New', monospace;
}

.result-actions { display: flex; gap: 8px; }
.action-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; border: 1px solid var(--border); border-radius: 10px;
  background: var(--surface); cursor: pointer; font-size: 13px; color: var(--text-secondary);
  transition: var(--transition); font-weight: 500;
}
.action-btn:hover { border-color: var(--border); background: var(--surface-hover); color: var(--text); }
.action-btn--primary { background: var(--text); color: #fff; border-color: var(--text); }
.action-btn--primary:hover { background: #333; border-color: #333; }

/* ========== 底部输入区 ========== */
.input-wrapper {
  flex-shrink: 0; padding: 16px 24px 24px; background: var(--bg);
  border-top: 1px solid var(--border-light);
}
.input-container { max-width: 780px; margin: 0 auto; }
.type-picker {
  display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap;
}
.type-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 7px 14px; border: 1px solid var(--border); border-radius: 20px;
  background: var(--surface); cursor: pointer; font-size: 13px; color: var(--text-muted);
  transition: var(--transition); font-weight: 450;
}
.type-btn:hover { border-color: var(--border); color: var(--text-secondary); }
.type-btn.active { background: var(--text); color: #fff; border-color: var(--text); }
.input-box {
  display: flex; align-items: flex-end;
  background: var(--surface); border: 1.5px solid var(--border); border-radius: var(--radius-lg);
  padding: 8px 8px 8px 20px; transition: all 0.25s ease;
  box-shadow: var(--shadow-sm);
}
.input-box:focus-within { border-color: var(--text-muted); box-shadow: 0 0 0 3px rgba(0,0,0,0.05); }
.input-box textarea {
  flex: 1; border: none; outline: none; resize: none;
  font-size: 14px; font-family: inherit; line-height: 1.5;
  padding: 8px 0; max-height: 120px; background: transparent; color: var(--text);
}
.input-box textarea::placeholder { color: var(--text-muted); }
.send-btn {
  width: 40px; height: 40px; border-radius: 12px; border: none;
  background: var(--text); color: #fff; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: var(--transition);
}
.send-btn:hover { background: #333; }
.send-btn:disabled { background: var(--border); cursor: not-allowed; }
.input-hint { text-align: center; font-size: 12px; color: var(--text-muted); margin-top: 10px; }

/* ========== Toast 通知 ========== */
.toast-notice {
  position: fixed; top: 24px; left: 50%; transform: translateX(-50%) translateY(-8px);
  background: var(--text); color: #fff; padding: 10px 24px; border-radius: 10px;
  font-size: 13px; font-weight: 500; z-index: 9999; opacity: 0;
  transition: all 0.3s ease; box-shadow: var(--shadow-lg);
  pointer-events: none;
}
.toast-notice--visible { opacity: 1; transform: translateX(-50%) translateY(0); }

/* ========== 响应式 ========== */
@media (max-width: 640px) {
  .feature-grid { grid-template-columns: 1fr; max-width: 320px; }
  .msg-row { max-width: 95%; }
  .messages { padding: 16px 12px; }
  .input-wrapper { padding: 12px 12px 16px; }
  .type-btn span:last-child { display: none; }
  .type-btn { padding: 8px 10px; }
}
</style>
