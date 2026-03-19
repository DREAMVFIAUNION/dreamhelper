export interface AuthUser {
  id: string
  email: string
  username: string
  displayName: string | null
  avatarUrl: string | null
  tierLevel: number
  emailVerified: boolean
}

export interface AuthState {
  user: AuthUser | null
  loading: boolean
}

export interface LoginParams {
  email: string
  password: string
}

export interface RegisterParams {
  email: string
  username: string
  password: string
  captchaVerifyToken: string
}

export interface AuthContextValue extends AuthState {
  login: (params: LoginParams) => Promise<{ success: boolean; errors?: string[] }>
  register: (params: RegisterParams) => Promise<{ success: boolean; errors?: string[] }>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}
