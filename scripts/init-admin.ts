// ═══ 管理员初始化脚本 ═══
// 用法: npx tsx scripts/init-admin.ts
// 环境变量: ADMIN_EMAIL, ADMIN_PASSWORD (可选，有默认值)

import { hashPassword } from '@dreamhelp/auth'
import { prisma } from '@dreamhelp/database'

async function initAdmin() {
  const email = process.env.ADMIN_EMAIL || 'admin@dreamvfia.com'
  const password = process.env.ADMIN_PASSWORD || 'Admin@2026'

  console.log('═══════════════════════════════════════')
  console.log('  DREAMVFIA · 超级管理员初始化')
  console.log('═══════════════════════════════════════')

  const existing = await prisma.user.findUnique({ where: { email } })
  if (existing) {
    console.log(`\n⚠ 管理员账号已存在: ${email}`)
    console.log(`  ID: ${existing.id}`)
    console.log(`  tierLevel: ${existing.tierLevel}`)

    if (existing.tierLevel < 10) {
      console.log('\n  提升为超级管理员 (tierLevel=10)...')
      await prisma.user.update({
        where: { id: existing.id },
        data: {
          tierLevel: 10,
          metadata: {
            ...(existing.metadata as Record<string, unknown> || {}),
            adminRole: 'super_admin',
          },
        },
      })
      console.log('  ✓ 已提升')
    }

    return
  }

  const passwordHash = await hashPassword(password)

  const admin = await prisma.user.create({
    data: {
      email,
      username: 'admin',
      displayName: '超级管理员',
      passwordHash,
      status: 'active',
      tierLevel: 10,
      emailVerified: true,
      metadata: {
        adminRole: 'super_admin',
        createdBy: 'system',
        failedAttempts: 0,
      },
      settings: { theme: 'dark', language: 'zh-CN' },
    },
  })

  console.log(`\n✓ 超级管理员创建成功`)
  console.log(`  邮箱: ${admin.email}`)
  console.log(`  用户名: ${admin.username}`)
  console.log(`  ID: ${admin.id}`)
  console.log(`\n⚠ 请立即修改默认密码！`)
  console.log('═══════════════════════════════════════')
}

initAdmin()
  .catch((err) => {
    console.error('初始化失败:', err)
    process.exit(1)
  })
  .finally(() => void prisma.$disconnect())
