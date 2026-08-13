export type Score = { home: number; away: number }
const outcome = (s: Score) => Math.sign(s.home - s.away)
export function calculatePredictionPoints(actual: Score, prediction: Score): number {
  if (actual.home === prediction.home && actual.away === prediction.away) return 5
  if (outcome(actual) !== outcome(prediction)) return 0
  return 2 + (actual.home - actual.away === prediction.home - prediction.away ? 1 : 0)
}
export const isPredictionLocked = (matchDate: Date, status: string) => status !== 'postponed' && matchDate.getTime() <= Date.now()
