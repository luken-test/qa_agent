import { marked } from 'marked'

export function renderMd(text) {
  if (!text) return ''
  return marked.parse(text, { breaks: true })
}
