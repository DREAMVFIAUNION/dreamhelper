/**
 * DataLoader 批处理（第五章 5.3.2）
 */
import { Injectable, Scope } from '@nestjs/common'

@Injectable({ scope: Scope.REQUEST })
export class AgentDataLoader {
  // TODO: 接入 DataLoader + Prisma
  async loadById(id: string) {
    // TODO: 批量加载 Agent
    return null
  }

  async loadByIds(ids: string[]) {
    // TODO: 批量加载多个 Agent
    return []
  }
}
