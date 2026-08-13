import { describe, expect, it } from 'vitest'
import { calculatePredictionPoints, isPredictionLocked } from './scoring'
describe('calculatePredictionPoints', () => { const actual = { home: 3, away: 1 }; it.each([[3,1,5],[2,0,3],[2,1,2],[1,0,2],[1,1,0],[0,1,0]])('%i-%i', (home, away, points) => expect(calculatePredictionPoints(actual, { home, away })).toBe(points)); it.each([[2,2,5],[1,1,3],[3,3,3],[2,1,0]])('draw %i-%i', (home, away, points) => expect(calculatePredictionPoints({ home: 2, away: 2 }, { home, away })).toBe(points)); })
describe('isPredictionLocked', () => { it('uses server date semantics', () => { expect(isPredictionLocked(new Date(Date.now() - 1), 'scheduled')).toBe(true); expect(isPredictionLocked(new Date(Date.now() - 1), 'postponed')).toBe(false) }) })
