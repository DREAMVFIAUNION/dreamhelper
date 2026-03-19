import { getRequestConfig } from 'next-intl/server'
import { cookies, headers } from 'next/headers'

export const locales = ['zh-CN', 'en'] as const
export type Locale = (typeof locales)[number]
export const defaultLocale: Locale = 'zh-CN'

export default getRequestConfig(async () => {
  // 优先读取 cookie，其次 Accept-Language header
  const cookieStore = await cookies()
  const headerStore = await headers()
  let locale: Locale = defaultLocale

  const cookieLocale = cookieStore.get('locale')?.value
  if (cookieLocale && locales.includes(cookieLocale as Locale)) {
    locale = cookieLocale as Locale
  } else {
    const acceptLang = headerStore.get('accept-language') || ''
    if (acceptLang.includes('en')) {
      locale = 'en'
    }
  }

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  }
})
