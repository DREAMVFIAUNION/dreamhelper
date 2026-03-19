'use client'

import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import type { AuthContextValue, AuthUser, LoginParams, RegisterParams } from './types'

const DASHBOARD_PATHS = ['/overview', '/chat', '/agents', '/knowledge', '/analytics', '/settings', '/workflows', '/channels', '/verify']

const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  return res.json() as Promise<T>
}

interface MeResponse {
  success: boolean
  user?: AuthUser
  error?: string
}

interface AuthResponse {
  success: boolean
  user?: AuthUser
  errors?: string[]
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const pathname = usePathname()
  const router = useRouter()

  const refreshUser = useCallback(async () => {
    try {
      const data = await apiFetch<MeResponse>('/api/auth/me')
      setUser(data.success && data.user ? data.user : null)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshUser()
  }, [refreshUser])

  // 当 token 失效 (user=null) 且在 dashboard 页面时，自动跳转登录
  useEffect(() => {
    if (!loading && !user && DASHBOARD_PATHS.some(p => pathname === p || pathname.startsWith(p + '/'))) {
      router.replace('/login')
    }
  }, [loading, user, pathname, router])

  const login = useCallback(
    async (params: LoginParams): Promise<{ success: boolean; errors?: string[] }> => {
      const data = await apiFetch<AuthResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(params),
      })
      if (data.success && data.user) {
        setUser(data.user)
      }
      return { success: data.success, errors: data.errors }
    },
    [],
  )

  const register = useCallback(
    async (params: RegisterParams): Promise<{ success: boolean; errors?: string[] }> => {
      const data = await apiFetch<AuthResponse>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(params),
      })
      if (data.success && data.user) {
        setUser(data.user)
      }
      return { success: data.success, errors: data.errors }
    },
    [],
  )

  const logout = useCallback(async () => {
    await apiFetch('/api/auth/logout', { method: 'POST' })
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}
