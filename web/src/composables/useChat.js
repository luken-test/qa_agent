import { ref, computed } from 'vue'
import { useChatStore } from '../stores/chat'
import { useModelStore } from '../stores/model'
import { submitJMeter, submitTestcases, submitBug, submitChat, submitQA, submitExecute, pollTask } from '../api'

export function useChat() {
  const chatStore = useChatStore()
  const modelStore = useModelStore()

  const inputText = ref('')
  const sending = ref(false)
  const taskType = ref(localStorage.getItem('qa_task_type') || '')

  const typePlaceholder = computed(() => {
    const map = {
      testcase: '输入需求描述，例如：用户登录功能，支持账号密码和手机验证码...',
      jmeter: '输入 curl 命令或接口文档内容...',
      bug: '描述 Bug 现象，例如：查询页面无响应，控制台报 500 错误...',
      qa: '输入测试相关问题，例如：什么是等价类划分法？JMeter如何做分布式压测？',
    }
    return map[taskType.value] || '请先选择上方的任务类型...'
  })

  function _buildSubmitFn(type, text) {
    const threadId = chatStore.currentThreadId
    const model = modelStore.selected
    const isUrl = /^https?:\/\//i.test(text.trim())

    const configs = {
      jmeter: { fn: submitJMeter, payload: { input: text, input_type: isUrl ? 'url' : 'text', model, thread_id: threadId } },
      bug: { fn: submitBug, payload: { description: text, model, thread_id: threadId } },
      testcase: { fn: submitTestcases, payload: { input: text, input_type: isUrl ? 'url' : 'text', model, thread_id: threadId } },
      qa: { fn: submitQA, payload: { question: text, model, thread_id: threadId } },
    }

    return configs[type] || { fn: submitChat, payload: { message: text, model, thread_id: threadId } }
  }

  function _parseResult(type, r, msg) {
    if (type === 'jmeter' && r.jmx_script) {
      msg.jmeter = r
      msg.stats = {
        http: (r.jmx_script.match(/<HTTPSamplerProxy/g) || []).length,
        assertions: (r.jmx_script.match(/<(ResponseAssertion|DurationAssertion|JSONPathAssertion)/g) || []).length,
        extractors: (r.jmx_script.match(/<(JSONPostProcessor|RegexExtractor)/g) || []).length,
      }
    } else if (type === 'testcase' && r.testcases_json) {
      msg.testcases = r
      try {
        const tc = JSON.parse(r.testcases_json)
        const modules = tc.topics || []
        msg.tcStats = { modules: modules.length, cases: modules.reduce((s, m) => s + (m.children || []).length, 0) }
      } catch { /* ignore */ }
    } else if (type === 'bug' && r.bug_report_md) {
      msg.bug = r
    } else if (r.chat_response) {
      msg.chat = r
    } else if (r.output_json) {
      msg.text = '测试用例已生成，文件路径：' + r.output_json
    } else {
      msg.text = '任务已完成。'
    }
  }

  async function send(evt) {
    const text = inputText.value.trim()
    if (!text || sending.value || !taskType.value) return
    if (evt?.shiftKey) return

    inputText.value = ''
    chatStore.addMessage({ role: 'user', content: text })
    chatStore.updateTitle(text)

    sending.value = true
    const type = taskType.value
    chatStore.addMessage({ role: 'assistant', loading: true })

    try {
      localStorage.setItem('qa_model', modelStore.selected)
      const { fn, payload } = _buildSubmitFn(type, text)
      const { data } = await fn(payload)
      const result = await pollTask(data.task_id)
      const r = result.result || {}

      chatStore.updateLastMessage((msg) => {
        msg.loading = false
        if (r.error) { msg.error = r.error; return }
        _parseResult(type, r, msg)
      })
    } catch (e) {
      chatStore.updateLastMessage((msg) => { msg.loading = false; msg.error = e.message || '请求失败' })
    } finally {
      sending.value = false
    }
  }

  function setTaskType(type) {
    taskType.value = type
    if (type) localStorage.setItem('qa_task_type', type)
  }

  function quickInput(type) {
    setTaskType(type)
    const examples = {
      jmeter: "curl 'https://api.example.com/users' -H 'Authorization: Bearer token' -H 'Content-Type: application/json'",
      testcase: '请为用户登录功能生成测试用例，包括正常登录、密码错误、账号不存在等场景',
      bug: '页面查询无响应，点击搜索按钮后加载超过30秒，浏览器控制台报 500 错误',
      qa: 'Playwright 和 Selenium 有什么区别？各有什么优缺点？',
    }
    inputText.value = examples[type] || ''
  }

  return { inputText, sending, taskType, typePlaceholder, send, setTaskType, quickInput }
}

/** 独立函数：从测试用例结果卡片触发执行 */
export async function executeTestCases(testcasesJson) {
  const chatStore = useChatStore()
  const modelStore = useModelStore()

  chatStore.addMessage({ role: 'user', content: '执行测试用例' })
  chatStore.addMessage({ role: 'assistant', loading: true })

  try {
    const { data } = await submitExecute({
      testcases_json: testcasesJson,
      model: modelStore.selected,
      thread_id: chatStore.currentThreadId,
    })
    const result = await pollTask(data.task_id)
    const r = result.result || {}

    chatStore.updateLastMessage((msg) => {
      msg.loading = false
      if (r.error) { msg.error = r.error; return }
      msg.execution = r
    })
  } catch (e) {
    chatStore.updateLastMessage((msg) => { msg.loading = false; msg.error = e.message || '执行失败' })
  }
}
