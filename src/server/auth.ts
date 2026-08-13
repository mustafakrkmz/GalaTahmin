import { authenticateRequest, clerkClient } from '@clerk/express'
import { eq } from 'drizzle-orm'
import { db } from '../db'
import { users } from '../db/schema'

type RequestLike = { headers: Record<string, string | string[] | undefined> }
export async function currentUser(req: RequestLike) {
  const state = await authenticateRequest({ clerkClient, request: req as never })
  if (!state.isAuthenticated) return null
  const userId = state.toAuth().userId
  const [existing] = await db.select().from(users).where(eq(users.clerkUserId, userId)).limit(1)
  if (existing) return existing
  const [created] = await db.insert(users).values({ clerkUserId: userId, displayName: 'Yeni oyuncu' }).returning()
  return created
}
export async function requireUser(req: RequestLike) { const user = await currentUser(req); if (!user) throw new ApiError(401, 'Giriş yapmanız gerekiyor.'); return user }
export async function requireAdmin(req: RequestLike) { const user = await requireUser(req); if (user.role !== 'admin') throw new ApiError(403, 'Bu işlem için yönetici yetkisi gerekli.'); return user }
export class ApiError extends Error { constructor(public status: number, message: string) { super(message) } }
