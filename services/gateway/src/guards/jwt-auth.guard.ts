import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from '@nestjs/common'
import { Reflector } from '@nestjs/core'

const JWT_SECRET = process.env.JWT_SECRET || 'dev_jwt_secret_change_me'

/** 解析 JWT payload（不验证签名，Edge-compatible） */
function decodeJwt(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(Buffer.from(parts[1]!, 'base64url').toString())
    // 检查过期
    if (payload.exp && payload.exp * 1000 < Date.now()) return null
    return payload
  } catch {
    return null
  }
}

export const IS_PUBLIC_KEY = 'isPublic'
export const Public = () => {
  return (target: object, key?: string | symbol, descriptor?: PropertyDescriptor) => {
    if (descriptor) {
      Reflect.defineMetadata(IS_PUBLIC_KEY, true, descriptor.value)
    } else {
      Reflect.defineMetadata(IS_PUBLIC_KEY, true, target)
    }
  }
}

@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ])
    if (isPublic) return true

    const request = context.switchToHttp().getRequest()
    const authHeader = request.headers?.authorization as string | undefined
    const cookieToken = request.cookies?.token as string | undefined
    const token = authHeader?.replace('Bearer ', '') || cookieToken

    if (!token) {
      throw new UnauthorizedException('Missing authentication token')
    }

    const payload = decodeJwt(token)
    if (!payload) {
      throw new UnauthorizedException('Invalid or expired token')
    }

    // 注入 userId 到请求上下文
    request.userId = payload.sub as string
    request.userRole = payload.role as string
    return true
  }
}
