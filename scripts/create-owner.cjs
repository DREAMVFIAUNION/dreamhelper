const { PrismaClient } = require('../packages/database/node_modules/@prisma/client')
const { pbkdf2, randomBytes } = require('node:crypto')
const { promisify } = require('node:util')

const pbk = promisify(pbkdf2)
const prisma = new PrismaClient()

async function main() {
  const salt = randomBytes(32).toString('hex')
  const hash = await pbk('Drv123123', salt, 100000, 64, 'sha512')
  const pw = salt + ':' + hash.toString('hex')

  const user = await prisma.user.create({
    data: {
      email: 'dreamvfiaunion@gmail.com',
      username: 'dreamvfia',
      displayName: 'DREAMVFIA',
      passwordHash: pw,
      status: 'active',
      tierLevel: 99,
      emailVerified: true,
      settings: { theme: 'dark', language: 'zh-CN' },
    },
  })
  console.log('✅ Created:', user.email, user.id)
}

main()
  .catch(e => { console.error('❌', e); process.exit(1) })
  .finally(() => prisma.$disconnect())
