/**
 * Lighthouse CI 配置 — 前端性能/可访问性/SEO 自动化检查
 *
 * 使用: npx lhci autorun
 * CI集成: GitHub Actions / GitLab CI
 */
module.exports = {
  ci: {
    collect: {
      // 使用 Next.js 生产构建
      startServerCommand: 'npm run start',
      startServerReadyPattern: 'Ready in',
      startServerReadyTimeout: 30000,
      url: [
        'http://localhost:3000/',           // 首页
        'http://localhost:3000/login',      // 登录页
        'http://localhost:3000/features',   // 功能页
        'http://localhost:3000/pricing',    // 定价页
      ],
      numberOfRuns: 3,
      settings: {
        preset: 'desktop',
        // 跳过需要认证的页面
        skipAudits: ['uses-http2'],
      },
    },
    assert: {
      assertions: {
        // 性能: ≥70 (SSR 页面合理基线)
        'categories:performance': ['warn', { minScore: 0.7 }],
        // 可访问性: ≥90 (严格要求)
        'categories:accessibility': ['error', { minScore: 0.9 }],
        // 最佳实践: ≥85
        'categories:best-practices': ['warn', { minScore: 0.85 }],
        // SEO: ≥80
        'categories:seo': ['warn', { minScore: 0.8 }],

        // 关键性能指标
        'first-contentful-paint': ['warn', { maxNumericValue: 3000 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 4000 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 500 }],

        // 可访问性硬性要求
        'color-contrast': 'error',
        'document-title': 'error',
        'html-has-lang': 'error',
        'image-alt': 'error',
        'label': 'error',
        'link-name': 'error',
        'meta-viewport': 'error',
      },
    },
    upload: {
      // 本地临时存储 (CI 中可改为 Lighthouse CI Server)
      target: 'temporary-public-storage',
    },
  },
}
