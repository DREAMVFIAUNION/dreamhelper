import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'
import { getEmailLogs } from '@/lib/email/email-logs'

const getSecret = () => {
  const s = process.env.JWT_SECRET
  if (!s && process.env.NODE_ENV === 'production') throw new Error('JWT_SECRET is required')
  return new TextEncoder().encode(s || 'dev-secret-do-not-use-in-production')
}

// ═══ GET /api/admin/email/history ═══

export async function GET(req: NextRequest) {
  const token = req.cookies.get('token')?.value
  if (!token) {
    return NextResponse.json({ success: false, error: '未登录' }, { status: 401 })
  }

  try {
    const { payload } = await jwtVerify(token, getSecret(), { issuer: 'dreamhelp' })
    const role = (payload as Record<string, unknown>).role as string | undefined
    if (role !== 'super_admin' && role !== 'admin') {
      return NextResponse.json({ success: false, error: '需要管理员权限' }, { status: 403 })
    }
  } catch {
    return NextResponse.json({ success: false, error: 'Token 无效' }, { status: 401 })
  }

  const logs = getEmailLogs()
  return NextResponse.json({
    success: true,
    logs,
    total: logs.length,
  })
}
