'use client'

import { useMemo, useEffect, useRef, useCallback } from 'react'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import sql from 'highlight.js/lib/languages/sql'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import yaml from 'highlight.js/lib/languages/yaml'
import markdown from 'highlight.js/lib/languages/markdown'
import java from 'highlight.js/lib/languages/java'
import go from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import cpp from 'highlight.js/lib/languages/cpp'
import dockerfile from 'highlight.js/lib/languages/dockerfile'
import nginx from 'highlight.js/lib/languages/nginx'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('shell', bash)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('json', json)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('md', markdown)
hljs.registerLanguage('java', java)
hljs.registerLanguage('go', go)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('c', cpp)
hljs.registerLanguage('dockerfile', dockerfile)
hljs.registerLanguage('docker', dockerfile)
hljs.registerLanguage('nginx', nginx)

interface MarkdownContentProps {
  content: string
  className?: string
}

/**
 * Markdown 渲染器 — 语法高亮 + Mermaid + KaTeX + 代码复制
 * 支持: 代码块(高亮)、行内代码、粗体、斜体、链接、列表、标题、分割线、Mermaid、LaTeX
 */
export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const html = useMemo(() => {
    const raw = renderMarkdown(content)
    // M-1 安全审计: DOMPurify 消毒防止 XSS
    return DOMPurify.sanitize(raw, {
      ADD_ATTR: ['target', 'rel', 'class', 'style'],
      ALLOW_DATA_ATTR: false,
    })
  }, [content])

  const handleCopyClick = useCallback((e: MouseEvent) => {
    const btn = (e.target as HTMLElement).closest('.code-copy-btn')
    if (!btn) return
    const wrapper = btn.closest('.code-block-wrapper')
    const code = wrapper?.querySelector('code')?.textContent || ''
    navigator.clipboard.writeText(code).then(() => {
      btn.textContent = '已复制'
      setTimeout(() => { btn.textContent = '复制' }, 1500)
    })
  }, [])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    el.addEventListener('click', handleCopyClick as EventListener)

    // Mermaid 渲染
    const mermaidEls = el.querySelectorAll('.mermaid-pending')
    if (mermaidEls.length > 0) {
      import('mermaid').then((mod) => {
        mod.default.initialize({
          startOnLoad: false,
          theme: 'dark',
          themeVariables: {
            darkMode: true,
            background: '#0a0e1a',
            primaryColor: '#00f0ff',
            primaryTextColor: '#e0e0ff',
            primaryBorderColor: '#00f0ff',
            lineColor: '#00f0ff',
            secondaryColor: '#1a1e3a',
            tertiaryColor: '#0d1117',
            fontFamily: 'JetBrains Mono, monospace',
          },
          flowchart: { curve: 'basis', padding: 15 },
          sequence: { actorMargin: 50, messageMargin: 40 },
        })
        mermaidEls.forEach(async (node, i) => {
          try {
            const id = `mermaid-${Date.now()}-${i}`
            const { svg } = await mod.default.render(id, node.textContent || '')
            node.innerHTML = DOMPurify.sanitize(svg, { USE_PROFILES: { svg: true, svgFilters: true } })
            node.classList.remove('mermaid-pending')
            node.classList.add('mermaid-rendered')
          } catch {
            node.classList.add('mermaid-error')
          }
        })
      })
    }

    return () => {
      el.removeEventListener('click', handleCopyClick as EventListener)
    }
  }, [html, handleCopyClick])

  return (
    <div
      ref={containerRef}
      className={`markdown-content ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function highlightCode(code: string, lang: string): string {
  const trimmed = code.trimEnd()
  if (lang && hljs.getLanguage(lang)) {
    try {
      return hljs.highlight(trimmed, { language: lang }).value
    } catch {
      // fallback
    }
  }
  // 自动检测
  try {
    return hljs.highlightAuto(trimmed).value
  } catch {
    return escapeHtml(trimmed)
  }
}

function renderKatex(tex: string, displayMode: boolean): string {
  try {
    const katex = require('katex')
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      output: 'html',
    })
  } catch {
    return escapeHtml(tex)
  }
}

function renderMarkdown(md: string): string {
  if (!md) return ''

  // 提取块级 LaTeX $$...$$ 占位
  const latexBlocks: string[] = []
  let text = md.replace(/\$\$([\s\S]*?)\$\$/g, (_match, tex: string) => {
    const idx = latexBlocks.length
    latexBlocks.push(renderKatex(tex.trim(), true))
    return `\x00LATEXBLOCK_${idx}\x00`
  })

  // 提取代码块，用占位符替换，最后再恢复
  const codeBlocks: string[] = []
  text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_match, lang: string, code: string) => {
    const idx = codeBlocks.length
    const langLower = lang.toLowerCase()

    // Mermaid 特殊处理
    if (langLower === 'mermaid') {
      codeBlocks.push(
        `<div class="mermaid-wrapper"><div class="mermaid-pending">${escapeHtml(code.trimEnd())}</div></div>`
      )
      return `\x00CODEBLOCK_${idx}\x00`
    }

    const langLabel = lang ? `<span class="code-lang">${escapeHtml(lang)}</span>` : ''
    const highlighted = highlightCode(code, langLower)
    codeBlocks.push(
      `<div class="code-block-wrapper">${langLabel}<button class="code-copy-btn" type="button">复制</button><pre class="code-block"><code class="hljs">${highlighted}</code></pre></div>`
    )
    return `\x00CODEBLOCK_${idx}\x00`
  })

  // 行内 LaTeX $...$（不匹配 $$）— 提取为占位符
  const inlineLatex: string[] = []
  text = text.replace(/(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)/g, (_match, tex: string) => {
    const idx = inlineLatex.length
    inlineLatex.push(renderKatex(tex, false))
    return `\x00INLINELATEX_${idx}\x00`
  })

  // XSS 防护: 转义 HTML 标签字符，防止注入（代码块/LaTeX 已被占位符保护）
  // 保留 > 以兼容 Markdown 引用块语法
  text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;')

  // 行内代码
  text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')

  // 表格 — 连续的 | 行解析为 <table>
  text = text.replace(/((?:^\|.+\|[ ]*$\n?)+)/gm, (_block: string) => {
    const rows = _block.trim().split('\n').filter(Boolean)
    if (rows.length < 2) return _block
    const parseRow = (row: string) =>
      row.replace(/^\||\|$/g, '').split('|').map((c) => c.trim())
    const header = parseRow(rows[0]!)
    // 检测分隔行（含 --- 或 :---: 等）
    const sepRow = parseRow(rows[1]!)
    const isSep = sepRow.every((c) => /^:?-{2,}:?$/.test(c))
    const dataStart = isSep ? 2 : 1
    const aligns = isSep
      ? sepRow.map((c) => {
          if (c.startsWith(':') && c.endsWith(':')) return 'center'
          if (c.endsWith(':')) return 'right'
          return 'left'
        })
      : header.map(() => 'left')
    let html = '<div class="md-table-wrap"><table class="md-table"><thead><tr>'
    header.forEach((h, i) => {
      html += `<th style="text-align:${aligns[i] || 'left'}">${h}</th>`
    })
    html += '</tr></thead><tbody>'
    for (let r = dataStart; r < rows.length; r++) {
      const cells = parseRow(rows[r]!)
      html += '<tr>'
      cells.forEach((c, i) => {
        html += `<td style="text-align:${aligns[i] || 'left'}">${c}</td>`
      })
      html += '</tr>'
    }
    html += '</tbody></table></div>'
    return html
  })

  // 引用块 > (连续行合并)
  text = text.replace(/((?:^>[ ]?.+$\n?)+)/gm, (_block: string) => {
    const inner = _block.replace(/^>[ ]?/gm, '').trim()
    return `<blockquote class="md-blockquote">${inner}</blockquote>`
  })

  // 标题 (h1-h4)
  text = text.replace(/^#### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
  text = text.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>')
  text = text.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>')
  text = text.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>')

  // 删除线
  text = text.replace(/~~(.+?)~~/g, '<del class="md-del">$1</del>')

  // 粗体+斜体
  text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // 链接（过滤 javascript: 协议 + 转义 URL 中的引号）
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_m: string, linkText: string, url: string) => {
    const safeUrl = url.replace(/"/g, '&quot;')
    if (safeUrl.trim().toLowerCase().startsWith('javascript:')) return linkText
    return `<a href="${safeUrl}" target="_blank" rel="noopener" class="md-link">${linkText}</a>`
  })

  // 分割线
  text = text.replace(/^---$/gm, '<hr class="md-hr" />')

  // 任务列表 - [x] / - [ ]
  text = text.replace(/^[\s]*- \[x\] (.+)$/gm, '<li class="md-task md-task-done"><span class="md-checkbox checked">✓</span> $1</li>')
  text = text.replace(/^[\s]*- \[ \] (.+)$/gm, '<li class="md-task"><span class="md-checkbox">☐</span> $1</li>')
  text = text.replace(/((?:<li class="md-task[^"]*">.*<\/li>\n?)+)/g, '<ul class="md-task-list">$1</ul>')

  // 无序列表
  text = text.replace(/^[\s]*[-*] (.+)$/gm, '<li class="md-li">$1</li>')
  text = text.replace(/((?:<li class="md-li">.*<\/li>\n?)+)/g, '<ul class="md-ul">$1</ul>')

  // 有序列表
  text = text.replace(/^\d+\. (.+)$/gm, '<li class="md-oli">$1</li>')
  text = text.replace(/((?:<li class="md-oli">.*<\/li>\n?)+)/g, '<ol class="md-ol">$1</ol>')

  // 段落 (连续非空行)
  text = text.replace(/^(?!<[huo1-9lr]|<div|<pre|<block|<table|\x00)(.+)$/gm, '<p class="md-p">$1</p>')

  // 恢复代码块
  text = text.replace(/\x00CODEBLOCK_(\d+)\x00/g, (_m, idx: string) => codeBlocks[parseInt(idx)] || '')

  // 恢复 LaTeX 块
  text = text.replace(/\x00LATEXBLOCK_(\d+)\x00/g, (_m, idx: string) => {
    const rendered = latexBlocks[parseInt(idx)] || ''
    return `<div class="katex-block">${rendered}</div>`
  })

  // 恢复行内 LaTeX
  text = text.replace(/\x00INLINELATEX_(\d+)\x00/g, (_m, idx: string) => inlineLatex[parseInt(idx)] || '')

  return text
}
