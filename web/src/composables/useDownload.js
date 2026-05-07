import { downloadFile as apiDownload } from '../api'

export function useDownload() {
  async function downloadFile(path) {
    if (!path) return
    const filename = path.split(/[/\\]/).pop()
    try {
      const { data } = await apiDownload(filename)
      const url = URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('下载失败，请从 output 目录手动获取: ' + path)
    }
  }

  function copyText(text) {
    navigator.clipboard.writeText(text)
    const toast = document.createElement('div')
    toast.textContent = '已复制到剪贴板'
    toast.className = 'toast-notice'
    document.body.appendChild(toast)
    requestAnimationFrame(() => { toast.classList.add('toast-notice--visible') })
    setTimeout(() => {
      toast.classList.remove('toast-notice--visible')
      setTimeout(() => toast.remove(), 300)
    }, 1500)
  }

  return { downloadFile, copyText }
}
