import { migrate } from 'drizzle-orm/neon-http/migrator'
import { db } from './index'

await migrate(db, { migrationsFolder: './drizzle' })
console.log('Migration tamamlandı.')
