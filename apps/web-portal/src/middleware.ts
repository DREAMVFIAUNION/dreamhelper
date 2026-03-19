import { NextRequest, NextResponse } from 'next/server'
import { jwtVerify } from 'jose'

const getSecret = () => {
  const secret = process.env.JWT_SECRET
  if (!secret && process.env.NODE_ENV === 'production') {
    throw new Error('JWT_SECRET environment variable is required in production')
  }
  return new TextEncoder().encode(secret || 'dev-secret-do-not-use-in-production')
}

const PUBLIC_PATHS = ['/', '/features', '/pricing', '/about']
const AUTH_PATHS = ['/login', '/register', '/forgot', '/reset']
const ADMIN_PREFIX = '/admin'
const ADMIN_LOGIN_PATH = '/admin/login'
const DASHBOARD_PATHS = ['/overview', '/chat', '/agents', '/knowledge', '/analytics', '/settings', '/workflows', '/channels', '/verify']

function isPublic(path: string) {
  return PUBLIC_PATHS.includes(path) || path.startsWith('/api/') || path.startsWith('/_next/')
}

function isAuthPage(path: string) {
  return AUTH_PATHS.includes(path)
}

function isDashboard(path: string) {
  return DASHBOARD_PATHS.some((p) => path === p || path.startsWith(p + '/'))
}

function isAdmin(path: string) {
  return path.startsWith(ADMIN_PREFIX) && path !== ADMIN_LOGIN_PATH
}

function isAdminLogin(path: string) {
  return path === ADMIN_LOGIN_PATH
}

/** 验证 JWT 签名并解析 payload（使用 jose 库，Edge Runtime 兼容） */
async function verifyAndParse(token: string): Promise<{ sub?: string; role?: string } | null> {
  try {
    const { payload } = await jwtVerify(token, getSecret(), { issuer: 'dreamhelp' })
    return { sub: payload.sub as string | undefined, role: (payload as Record<string, unknown>).role as string | undefined }
  } catch {
    return null
  }
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl
  const token = req.cookies.get('token')?.value

  if (isPublic(pathname)) {
    return NextResponse.next()
  }

  // 认证页面：已登录且 token 有效则重定向到 /overview
  if (isAuthPage(pathname)) {
    if (token) {
      const payload = await verifyAndParse(token)
      if (payload) {
        return NextResponse.redirect(new URL('/overview', req.url))
      }
      // token 无效/过期 → 清除 cookie，允许访问登录页
      const res = NextResponse.next()
      res.cookies.delete('token')
      return res
    }
    return NextResponse.next()
  }

  // 管理员登录页：已有 admin token 则重定向到 /admin
  if (isAdminLogin(pathname)) {
    if (token) {
      const payload = await verifyAndParse(token)
      if (payload?.role === 'admin' || payload?.role === 'super_admin') {
        return NextResponse.redirect(new URL('/admin', req.url))
      }
    }
    return NextResponse.next()
  }

  // 管理后台：需登录 + admin/super_admin 角色
  if (isAdmin(pathname)) {
    if (!token) {
      return NextResponse.redirect(new URL('/admin/login', req.url))
    }
    const payload = await verifyAndParse(token)
    if (!payload || (payload.role !== 'admin' && payload.role !== 'super_admin')) {
      return NextResponse.redirect(new URL('/overview', req.url))
    }
    return NextResponse.next()
  }

  // Dashboard：需登录且 token 有效
  if (isDashboard(pathname)) {
    if (!token) {
      const loginUrl = new URL('/login', req.url)
      loginUrl.searchParams.set('from', pathname)
      return NextResponse.redirect(loginUrl)
    }
    const payload = await verifyAndParse(token)
    if (!payload) {
      // token 无效 → 清除 cookie，重定向到登录
      const loginUrl = new URL('/login', req.url)
      loginUrl.searchParams.set('from', pathname)
      const res = NextResponse.redirect(loginUrl)
      res.cookies.delete('token')
      return res
    }
    return NextResponse.next()
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|logo|og-image).*)'],
}
