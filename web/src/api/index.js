import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 300000 })

export function submitJMeter(data) { return api.post('/jmeter', data) }
export function submitTestcases(data) { return api.post('/testcases', data) }
export function submitBug(data) { return api.post('/bug', data) }
export function submitChat(data) { return api.post('/chat', data) }
export function submitQA(data) { return api.post('/qa', data) }
export function submitExecute(data) { return api.post('/execute', data) }
export function getTaskStatus(taskId) { return api.get(`/tasks/${taskId}`) }
export function getTasks() { return api.get('/tasks') }
export function healthCheck() { return api.get('/health') }
export function downloadFile(filename) { return api.get(`/download/${filename}`, { responseType: 'blob' }) }
export function getThreads() { return api.get('/threads') }
export function getThreadHistory(threadId) { return api.get(`/history/${threadId}`) }

export function pollTask(taskId, onStatus, interval = 2000) {
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const { data } = await getTaskStatus(taskId)
        if (onStatus) onStatus(data)
        if (data.status === 'completed') { clearInterval(timer); resolve(data) }
        else if (data.status === 'failed') { clearInterval(timer); reject(new Error(data.error || '任务失败')) }
      } catch (e) { clearInterval(timer); reject(e) }
    }, interval)
  })
}
