-- Run once in the user's own Supabase SQL Editor for Nakitçe snapshot sync.
-- This is NOT the Miras Teknoloji membership project (see membership_schema.sql).

create table if not exists public.nakitce_snapshots (
    user_id uuid primary key references auth.users (id) on delete cascade,
    records jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

alter table public.nakitce_snapshots enable row level security;

drop policy if exists "read own Nakitçe snapshot" on public.nakitce_snapshots;
create policy "read own Nakitçe snapshot"
    on public.nakitce_snapshots for select
    using (auth.uid() = user_id);

drop policy if exists "insert own Nakitçe snapshot" on public.nakitce_snapshots;
create policy "insert own Nakitçe snapshot"
    on public.nakitce_snapshots for insert
    with check (auth.uid() = user_id);

drop policy if exists "update own Nakitçe snapshot" on public.nakitce_snapshots;
create policy "update own Nakitçe snapshot"
    on public.nakitce_snapshots for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- Optional migration if an older ustakasa_snapshots table already exists:
-- insert into public.nakitce_snapshots (user_id, records, updated_at)
-- select user_id, records, updated_at from public.ustakasa_snapshots
-- on conflict (user_id) do nothing;
