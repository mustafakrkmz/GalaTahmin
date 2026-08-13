import { boolean, index, integer, pgEnum, pgTable, timestamp, uniqueIndex, uuid, varchar } from 'drizzle-orm/pg-core'

export const userRole = pgEnum('user_role', ['user', 'admin'])
export const matchStatus = pgEnum('match_status', ['scheduled', 'live', 'finished', 'postponed', 'cancelled'])

export const users = pgTable('users', {
  id: uuid('id').defaultRandom().primaryKey(), clerkUserId: varchar('clerk_user_id', { length: 255 }).notNull(),
  displayName: varchar('display_name', { length: 120 }).notNull(), avatarUrl: varchar('avatar_url', { length: 1000 }),
  role: userRole('role').notNull().default('user'), createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(), updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => [uniqueIndex('users_clerk_user_id_uq').on(t.clerkUserId)])

export const matches = pgTable('matches', {
  id: uuid('id').defaultRandom().primaryKey(), apiFixtureId: integer('api_fixture_id').notNull(),
  competitionId: integer('competition_id').notNull(), competitionName: varchar('competition_name', { length: 255 }).notNull(), season: integer('season').notNull(), round: varchar('round', { length: 255 }),
  matchDate: timestamp('match_date', { withTimezone: true }).notNull(), homeTeamId: integer('home_team_id').notNull(), homeTeamName: varchar('home_team_name', { length: 120 }).notNull(), awayTeamId: integer('away_team_id').notNull(), awayTeamName: varchar('away_team_name', { length: 120 }).notNull(),
  homeScore: integer('home_score'), awayScore: integer('away_score'), status: matchStatus('status').notNull().default('scheduled'), isFinished: boolean('is_finished').notNull().default(false), isActive: boolean('is_active').notNull().default(true), manualOverride: boolean('manual_override').notNull().default(false),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(), updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => [uniqueIndex('matches_api_fixture_id_uq').on(t.apiFixtureId), index('matches_match_date_idx').on(t.matchDate)])

export const predictions = pgTable('predictions', {
  id: uuid('id').defaultRandom().primaryKey(), matchId: uuid('match_id').notNull().references(() => matches.id, { onDelete: 'cascade' }), userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  predictedHomeScore: integer('predicted_home_score').notNull(), predictedAwayScore: integer('predicted_away_score').notNull(), createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(), updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => [uniqueIndex('predictions_match_user_uq').on(t.matchId, t.userId), index('predictions_match_idx').on(t.matchId), index('predictions_user_idx').on(t.userId)])
