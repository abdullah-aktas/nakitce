-- Nakitçe membership Supabase (Miras Teknoloji managed project)
-- Separate from the user-owned snapshot sync project.
-- Users may SELECT their own row only. All writes go through Edge Functions
-- with the service_role key (never ship that key in the Flet app).

create table if not exists public.memberships (
    user_id uuid primary key references auth.users (id) on delete cascade,
    email text,
    plan text not null default 'basic'
        check (plan in ('basic', 'trial', 'premium')),
    trial_started_at timestamptz,
    trial_ends_at timestamptz,
    premium_active boolean not null default false,
    premium_ends_at timestamptz,
    play_product_id text,
    play_purchase_token text,
    play_order_id text,
    play_status text,
    email_verified_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists memberships_premium_ends_at_idx
    on public.memberships (premium_ends_at);

alter table public.memberships enable row level security;

drop policy if exists "read own membership" on public.memberships;
create policy "read own membership"
    on public.memberships for select
    using (auth.uid() = user_id);

-- No insert/update/delete policies for authenticated users.
-- Edge Function uses service_role and bypasses RLS.

create or replace function public.set_memberships_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists memberships_set_updated_at on public.memberships;
create trigger memberships_set_updated_at
    before update on public.memberships
    for each row execute function public.set_memberships_updated_at();
