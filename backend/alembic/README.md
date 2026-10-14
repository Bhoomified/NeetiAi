# Database migrations (Alembic)

All schema changes go through Alembic. The API never runs `create_all` against
Postgres (local SQLite still uses it for tests/dev). `GET /health/ready` reports
`migrations: ...` while the database is behind the code.

Run every command from `backend/` (uses `DATABASE_URL` from `backend/.env`).

## One-time: adopt Alembic on the existing Supabase database

The production schema was created by `create_all`, so it already matches
`0001_baseline` (verified column-by-column on 2026-10-14). Mark it as such, then
apply everything after it:

```bash
venv/bin/alembic upgrade 0001_baseline:head --sql > 0002_preview.sql  # optional: review the SQL first (no DB connection)
venv/bin/alembic stamp 0001_baseline   # records the revision; changes nothing else
venv/bin/alembic upgrade head          # applies 0002
venv/bin/alembic current               # should print 0002_integrity_indexes_utc (head)
```

`stamp` must target `0001_baseline`, never `head`: stamping head would skip 0002.

### What 0002 changes

- unique `user.supabase_uid`, `user_id` foreign keys, the per-user indexes, and a
  unique `(user_id, symbol)` on the watchlist
- timestamps become `timestamptz`, reading the existing naive values as UTC (they were
  written with `utcnow()`), so the instant each row records stays the same
- Row Level Security on every table (makes `migrations/manual/0001_enable_rls.sql` redundant)

### Orphan rows (decide before validating the foreign keys)

On 2026-10-14 there were 5 `transaction` rows and 1 `incomesource` row whose
`user_id` has no matching user, left over from before login existed. 0002 adds
the foreign keys as `NOT VALID`: new rows are checked, these old ones are left
alone. To inspect them:

```sql
select t.* from "transaction" t left join "user" u on u.id = t.user_id where u.id is null;
select i.* from incomesource i left join "user" u on u.id = i.user_id where u.id is null;
```

After you delete them (or reassign them to a real user), finish the job:

```sql
ALTER TABLE "transaction"       VALIDATE CONSTRAINT transaction_user_id_fkey;
ALTER TABLE incomesource        VALIDATE CONSTRAINT incomesource_user_id_fkey;
ALTER TABLE budget              VALIDATE CONSTRAINT budget_user_id_fkey;
ALTER TABLE chatlog             VALIDATE CONSTRAINT chatlog_user_id_fkey;
ALTER TABLE investmentwatchlist VALIDATE CONSTRAINT investmentwatchlist_user_id_fkey;
```

## Making a schema change

1. Edit `app/models/__init__.py`.
2. `venv/bin/alembic revision --autogenerate -m "short description"`
3. Read the generated file; autogenerate misses renames, data moves, and RLS.
   Every new table needs `op.execute('ALTER TABLE "<name>" ENABLE ROW LEVEL SECURITY')`.
4. `venv/bin/alembic upgrade head` locally, run the tests, commit model + migration together.

Never delete a migration that has run anywhere; write a new one that reverses it.
