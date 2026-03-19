/**
 * PWA Service Worker 注册
 * 在客户端 layout 中调用，仅在生产环境注册
 */
export function registerServiceWorker() {
  if (typeof window === 'undefined') return
  if (!('serviceWorker' in navigator)) return

  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      })
      console.log('[PWA] SW registered, scope:', registration.scope)

      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (!newWorker) return
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'activated' && navigator.serviceWorker.controller) {
            console.log('[PWA] New version available')
          }
        })
      })
    } catch (err) {
      console.warn('[PWA] SW registration failed:', err)
    }
  })
}
