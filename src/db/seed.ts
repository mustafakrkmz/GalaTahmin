import { db } from './index'
import { matches } from './schema'

const now = Date.now()
await db.insert(matches).values([
  { apiFixtureId: 900001, competitionId: 203, competitionName: 'Süper Lig', season: 2026, round: '1. Hafta', matchDate: new Date(now + 7 * 86400000), homeTeamId: 645, homeTeamName: 'Galatasaray', awayTeamId: 611, awayTeamName: 'Fenerbahçe' },
  { apiFixtureId: 900002, competitionId: 203, competitionName: 'Süper Lig', season: 2026, round: '2. Hafta', matchDate: new Date(now + 14 * 86400000), homeTeamId: 549, homeTeamName: 'Beşiktaş', awayTeamId: 645, awayTeamName: 'Galatasaray' },
  { apiFixtureId: 900003, competitionId: 203, competitionName: 'Süper Lig', season: 2026, round: '3. Hafta', matchDate: new Date(now + 21 * 86400000), homeTeamId: 645, homeTeamName: 'Galatasaray', awayTeamId: 998, awayTeamName: 'Trabzonspor' },
]).onConflictDoNothing()
console.log('Örnek fikstür eklendi.')
