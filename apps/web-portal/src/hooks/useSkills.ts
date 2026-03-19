'use client'

import { useState, useCallback, useEffect } from 'react'

export interface SkillInfo {
  name: string
  description: string
  category: string
  version: string
  tags: string[]
  parameters: Record<string, unknown>
}

export interface SkillResult {
  success: boolean
  error: string | null
  result: string | null
  skill?: string
}

interface UseSkillsReturn {
  skills: SkillInfo[]
  categories: Record<string, number>
  loading: boolean
  executing: boolean
  lastResult: SkillResult | null
  loadSkills: (query?: string, category?: string) => Promise<void>
  executeSkill: (name: string, params: Record<string, unknown>) => Promise<SkillResult>
}

export function useSkills(): UseSkillsReturn {
  const [skills, setSkills] = useState<SkillInfo[]>([])
  const [categories, setCategories] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [lastResult, setLastResult] = useState<SkillResult | null>(null)

  const loadSkills = useCallback(async (query?: string, category?: string) => {
    setLoading(true)
    try {
      let url = '/api/skills'
      if (query) {
        url += `?q=${encodeURIComponent(query)}`
      } else if (category) {
        url += `?category=${encodeURIComponent(category)}`
      }
      const res = await fetch(url, { credentials: 'include' })
      const data = (await res.json()) as { skills: SkillInfo[] }
      if (data.skills) {
        setSkills(data.skills)
        // 计算分类
        const cats: Record<string, number> = {}
        for (const s of data.skills) {
          cats[s.category] = (cats[s.category] || 0) + 1
        }
        setCategories(cats)
      }
    } catch {
      console.error('[skills] load failed')
    } finally {
      setLoading(false)
    }
  }, [])

  const executeSkill = useCallback(async (name: string, params: Record<string, unknown>): Promise<SkillResult> => {
    setExecuting(true)
    try {
      const res = await fetch('/api/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name, params }),
      })
      const data = (await res.json()) as SkillResult
      setLastResult(data)
      return data
    } catch {
      const err: SkillResult = { success: false, error: '网络错误', result: null }
      setLastResult(err)
      return err
    } finally {
      setExecuting(false)
    }
  }, [])

  // 初始化加载
  useEffect(() => {
    void loadSkills()
  }, [loadSkills])

  return { skills, categories, loading, executing, lastResult, loadSkills, executeSkill }
}
