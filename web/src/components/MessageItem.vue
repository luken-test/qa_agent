<template>
  <div class="msg-row" :class="msg.role === 'user' ? 'msg-row--user' : 'msg-row--ai'">
    <!-- 用户消息 -->
    <template v-if="msg.role === 'user'">
      <div class="msg-content msg-content--user">{{ msg.content }}</div>
      <div class="msg-avatar msg-avatar--user">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      </div>
    </template>
    <!-- AI 消息 -->
    <template v-else>
      <div class="msg-avatar msg-avatar--ai">
        <svg width="16" height="16" viewBox="0 0 120 120" fill="none">
          <path d="M60 22 L88 36 L88 64 Q88 82 60 98 Q32 82 32 64 L32 36 Z" stroke="#fff" stroke-width="6" stroke-linejoin="round" fill="none"/>
          <polyline points="46,58 56,70 76,48" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="msg-content msg-content--ai">
        <!-- 加载中 -->
        <div v-if="msg.loading" class="loading-indicator">
          <div class="loading-pulse"></div>
          <span class="loading-text">正在思考</span>
        </div>
        <!-- 错误 -->
        <div v-else-if="msg.error" class="msg-error">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
          <span>{{ msg.error }}</span>
        </div>
        <!-- 普通文本 -->
        <div v-else-if="msg.text" class="md-body" v-html="renderMd(msg.text)"></div>
        <!-- 对话/QA -->
        <div v-if="msg.chat" class="md-body" v-html="renderMd(msg.chat.chat_response)"></div>
        <!-- JMeter -->
        <div v-if="msg.jmeter" class="result-card">
          <div class="result-header">
            <span class="result-tag result-tag--jmeter">JMeter 脚本</span>
            <span v-if="msg.jmeter.project_name" class="result-name">{{ msg.jmeter.project_name }}</span>
          </div>
          <div class="result-stats" v-if="msg.stats">
            <div class="stat-item"><span class="stat-value">{{ msg.stats.http }}</span><span class="stat-label">HTTP 请求</span></div>
            <div class="stat-item"><span class="stat-value">{{ msg.stats.assertions }}</span><span class="stat-label">断言</span></div>
            <div class="stat-item"><span class="stat-value">{{ msg.stats.extractors }}</span><span class="stat-label">提取器</span></div>
          </div>
          <details class="code-details">
            <summary>查看 JMX XML</summary>
            <pre class="code-block"><code>{{ msg.jmeter.jmx_script }}</code></pre>
          </details>
          <div class="result-actions">
            <button class="action-btn action-btn--primary" @click="download(msg.jmeter.output_jmx)">下载 JMX</button>
            <button class="action-btn" @click="copy(msg.jmeter.jmx_script)">复制</button>
          </div>
        </div>
        <!-- 测试用例 -->
        <div v-if="msg.testcases" class="result-card">
          <div class="result-header">
            <span class="result-tag result-tag--testcase">测试用例</span>
            <span class="result-name">生成完成</span>
          </div>
          <div class="result-stats" v-if="msg.tcStats">
            <div class="stat-item"><span class="stat-value">{{ msg.tcStats.modules }}</span><span class="stat-label">模块</span></div>
            <div class="stat-item"><span class="stat-value">{{ msg.tcStats.cases }}</span><span class="stat-label">用例</span></div>
          </div>
          <div class="result-actions">
            <button class="action-btn action-btn--primary" v-if="msg.testcases.output_xmind" @click="download(msg.testcases.output_xmind)">下载 Xmind</button>
            <button class="action-btn action-btn--green" @click="executeTestCases(msg.testcases.testcases_json)">执行测试</button>
            <button class="action-btn" @click="copy(msg.testcases.testcases_json)">复制 JSON</button>
          </div>
        </div>
        <!-- 执行结果 -->
        <div v-if="msg.execution" class="result-card">
          <div class="result-header">
            <span class="result-tag result-tag--execute">测试执行</span>
            <span class="result-name">{{ msg.execution.execution_result ? '执行完成' : '执行中...' }}</span>
          </div>
          <details class="code-details" v-if="msg.execution.execution_result">
            <summary>查看执行日志</summary>
            <pre class="code-block"><code>{{ msg.execution.execution_result }}</code></pre>
          </details>
          <div class="result-actions" v-if="msg.execution.output_script">
            <button class="action-btn" @click="download(msg.execution.output_script)">下载脚本</button>
            <button class="action-btn" @click="copy(msg.execution.execution_result)">复制结果</button>
          </div>
        </div>
        <!-- Bug 报告 -->
        <div v-if="msg.bug" class="result-card">
          <div class="result-header"><span class="result-tag result-tag--bug">Bug 报告</span></div>
          <div class="md-body" v-html="renderMd(msg.bug.bug_report_md)"></div>
          <div class="result-actions">
            <button class="action-btn action-btn--primary" @click="copy(msg.bug.bug_report_md)">复制报告</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { renderMd } from '../utils/markdown'
import { useDownload } from '../composables/useDownload'
import { executeTestCases } from '../composables/useChat'

defineProps({ msg: { type: Object, required: true } })

const { downloadFile: download, copyText: copy } = useDownload()
</script>
