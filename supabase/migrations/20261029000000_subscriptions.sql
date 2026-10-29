-- =============================================================================
-- Nakitçe · Abonelik gelir altyapısı
--   * activation_codes : bayi / web satışı / kampanya için tek kullanımlık kodlar
--   * subscription_events : denetim ve kötüye kullanım sınırı (yalnızca service_role)
--   * app_consents : KVKK aydınlatma / açık rıza kayıtları
--   * memberships : abonelik kaynağı ve yenileme alanları
-- Hiçbir tabloya istemciden yazma izni verilmez; yazma Edge Function ile yapılır.
-- =============================================================================

alter table public.memberships
    add column if not exists source text
        check (source in ('trial', 'play', 'code', 'admin')),
    add column if not exists auto_renewing boolean not null default false,
    add column if not exists last_verified_at timestamptz;

-- Aynı Play belirteci iki hesaba bağlanamaz (hesap paylaşımı / sahtecilik).
create unique index if not exists memberships_play_token_uidx
    on public.memberships (play_purchase_token)
    where play_purchase_token is not null;

create table if not exists public.activation_codes (
    code text primary key,
    days integer not null check (days between 1 and 3660),
    batch text,
    note text,
    expires_at timestamptz,
    used_by uuid references auth.users (id) on delete set null,
    used_at timestamptz,
    created_at timestamptz not null default now()
);
create index if not exists activation_codes_batch_idx on public.activation_codes (batch);
alter table public.activation_codes enable row level security;
-- Politika yok: yalnızca service_role okuyup yazabilir.

create table if not exists public.subscription_events (
    id bigint generated always as identity primary key,
    user_id uuid,
    kind text not null,
    detail jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);
create index if not exists subscription_events_user_idx
    on public.subscription_events (user_id, kind, created_at desc);
alter table public.subscription_events enable row level security;

create table if not exists public.app_consents (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users (id) on delete cascade,
    kind text not null check (kind in ('privacy', 'terms', 'ocr_upload', 'marketing')),
    version text not null,
    accepted boolean not null default true,
    created_at timestamptz not null default now()
);
create index if not exists app_consents_user_idx on public.app_consents (user_id, kind);
alter table public.app_consents enable row level security;

drop policy if exists "read own consents" on public.app_consents;
create policy "read own consents"
    on public.app_consents for select
    using (auth.uid() = user_id);

-- Kod üretici: SQL Editor veya `supabase db query --linked` ile yöneticiler çalıştırır.
-- Örnek: select * from public.generate_activation_codes(50, 365, 'bayi-2026-11');
create or replace function public.generate_activation_codes(
    p_count integer,
    p_days integer,
    p_batch text default null,
    p_expires_at timestamptz default null
)
returns table (code text)
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    alphabet constant text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    candidate text;
    i integer := 0;
    j integer;
begin
    if p_count < 1 or p_count > 1000 then
        raise exception 'p_count 1-1000 arasında olmalı';
    end if;
    while i < p_count loop
        candidate := '';
        for j in 1..12 loop
            candidate := candidate ||
                substr(alphabet, 1 + (get_byte(gen_random_bytes(1), 0) % length(alphabet)), 1);
        end loop;
        candidate := substr(candidate, 1, 4) || '-' || substr(candidate, 5, 4) || '-' || substr(candidate, 9, 4);
        begin
            insert into public.activation_codes (code, days, batch, expires_at)
            values (candidate, p_days, p_batch, p_expires_at);
            i := i + 1;
            code := candidate;
            return next;
        exception when unique_violation then
            null;
        end;
    end loop;
end;
$$;

revoke all on function public.generate_activation_codes(integer, integer, text, timestamptz)
    from public, anon, authenticated;
grant execute on function public.generate_activation_codes(integer, integer, text, timestamptz)
    to service_role;

-- Yönetim görünümü: gelir takibi için kaynak ve durum kırılımı.
create or replace view public.nakitce_revenue_overview
with (security_invoker = true)
as
select
    coalesce(source, 'none') as source,
    plan,
    count(*) filter (where premium_active) as active_members,
    count(*) as total_members
from public.memberships
group by 1, 2;

comment on table public.activation_codes is 'Tek kullanımlık Premium kodları — yalnızca service_role';
comment on table public.subscription_events is 'Üyelik olay günlüğü ve deneme sınırı — yalnızca service_role';
comment on table public.app_consents is 'KVKK aydınlatma ve rıza kayıtları';
