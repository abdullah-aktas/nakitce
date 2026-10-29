-- =============================================================================
-- Nakitçe · Miras Teknoloji (tek Supabase projesi)
-- Uygulama: Auth + memberships (Premium) + nakitce_snapshots (bulut defter)
-- Son kullanıcı kendi proje açmaz. Bu SQL'i yalnızca geliştirici çalıştırır.
-- =============================================================================

create extension if not exists "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1) Üyelik / Premium (yazma yalnızca Edge Function + service_role)
-- -----------------------------------------------------------------------------
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

create or replace function public.set_updated_at()
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
    for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 2) İşletme defteri snapshot (uygulama eşitleme birimi)
-- -----------------------------------------------------------------------------
create table if not exists public.nakitce_snapshots (
    user_id uuid primary key references auth.users (id) on delete cascade,
    records jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default now()
);

create index if not exists nakitce_snapshots_updated_at_idx
    on public.nakitce_snapshots (updated_at desc);

alter table public.nakitce_snapshots enable row level security;

drop policy if exists "own snapshots select" on public.nakitce_snapshots;
create policy "own snapshots select"
    on public.nakitce_snapshots for select
    using (auth.uid() = user_id);

drop policy if exists "own snapshots insert" on public.nakitce_snapshots;
create policy "own snapshots insert"
    on public.nakitce_snapshots for insert
    with check (auth.uid() = user_id);

drop policy if exists "own snapshots update" on public.nakitce_snapshots;
create policy "own snapshots update"
    on public.nakitce_snapshots for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop trigger if exists nakitce_snapshots_set_updated_at on public.nakitce_snapshots;
create trigger nakitce_snapshots_set_updated_at
    before update on public.nakitce_snapshots
    for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 3) Yönetim görünümü (JSON açmadan hızlı bakış — uygulama kullanmaz)
-- -----------------------------------------------------------------------------
create or replace view public.nakitce_overview
with (security_invoker = true)
as
select
    s.user_id,
    m.email,
    m.plan,
    m.premium_active,
    coalesce((s.records->>'cash_balance')::numeric, 0) as cash_balance,
    jsonb_array_length(coalesce(s.records->'customers', '[]'::jsonb)) as customer_count,
    jsonb_array_length(coalesce(s.records->'transactions', '[]'::jsonb)) as transaction_count,
    s.updated_at as snapshot_updated_at
from public.nakitce_snapshots s
left join public.memberships m on m.user_id = s.user_id;

comment on table public.memberships is 'Premium / deneme — yazma Edge Function ile';
comment on table public.nakitce_snapshots is 'Cihaz bulut eşitlemesi — müşteri başına bir JSON defter';
comment on view public.nakitce_overview is 'Miras yönetim özeti; RLS snapshot üzerinden uygulanır';
