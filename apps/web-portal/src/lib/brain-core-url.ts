/**
 * brain-core URL 工具
 * Windows 上 Node.js fetch 对 localhost 可能解析到 IPv6 ::1 导致连接超时
 * 统一替换为 127.0.0.1 确保 IPv4 连接
 */
const _raw = process.env.BRAIN_CORE_URL || process.env.GATEWAY_URL || 'http://127.0.0.1:8000'
export const BRAIN_CORE_URL = _raw.replace('://localhost:', '://127.0.0.1:').replace('://localhost/', '://127.0.0.1/').replace(/:\/\/localhost$/, '://127.0.0.1')

/**
 * 统一 brain-core 请求工具 — 自动注入 BRAIN_API_KEY 认证头
 * 所有前端 API 代理路由应使用此函数替代原始 fetch
 */
export async function brainCoreFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = `${BRAIN_CORE_URL}${path}`
  const headers = new Headers(init?.headers)

  // 注入 API Key (生产环境必须)
  const apiKey = process.env.BRAIN_API_KEY
  if (apiKey) {
    headers.set('X-API-Key', apiKey)
  }

  // 默认不缓存
  if (!headers.has('Cache-Control')) {
    headers.set('Cache-Control', 'no-cache')
  }

  // Agent ReAct 循环可能需要 30-120 秒，设置足够的超时
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 120_000)

  try {
    return await fetch(url, { ...init, headers, cache: 'no-store', signal: controller.signal })
  } finally {
    clearTimeout(timeout)
  }
}
