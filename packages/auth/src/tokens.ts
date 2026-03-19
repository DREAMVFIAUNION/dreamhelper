import * as jose from 'jose'

export interface TokenPayload {
  sub: string
  email: string
  role: string
  orgId?: string
}

const getSecret = () => new TextEncoder().encode(process.env.JWT_SECRET ?? 'dev-secret')

export async function signToken(payload: TokenPayload, expiresIn = '7d'): Promise<string> {
  return new jose.SignJWT(payload as unknown as jose.JWTPayload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(expiresIn)
    .setIssuer('dreamhelp')
    .sign(getSecret())
}

export async function verifyToken(token: string): Promise<TokenPayload> {
  const { payload } = await jose.jwtVerify(token, getSecret(), { issuer: 'dreamhelp' })
  return payload as unknown as TokenPayload
}
