import { eq } from 'drizzle-orm'
import { db } from '../db'
import { matches } from '../db/schema'
import { fetchTeamFixtures } from './football'

export async function syncGalatasarayFixtures() { const fixtures = await fetchTeamFixtures(); for (const fixture of fixtures) { const [existing] = await db.select({ id: matches.id, manualOverride: matches.manualOverride }).from(matches).where(eq(matches.apiFixtureId, fixture.apiFixtureId)).limit(1); if (!existing) { await db.insert(matches).values(fixture); } else if (!existing.manualOverride) { await db.update(matches).set({ ...fixture, updatedAt: new Date() }).where(eq(matches.id, existing.id)); } } return fixtures.length }
