/**
 * Nakitçe · membership Edge Function
 *
 * Deploy: supabase functions deploy membership
 * Secrets (isteğe bağlı, Play için):
 *   GOOGLE_SERVICE_ACCOUNT_JSON  Play Developer API servis hesabı anahtarı (JSON)
 *   PLAY_PACKAGE_NAME            varsayılan com.mirasteknoloji.nakitce
 *
 * İstemci:
 *   { action: "status" }
 *   { action: "redeem_code", code }
 *   { action: "verify_play_purchase", purchase_token, product_id }
 *   { action: "record_consent", kind, version, accepted? }
 *   { action: "delete_account", confirm: "SIL" }
 */

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.1";

const TRIAL_DAYS = 30;
const DAY = 86_400_000;
const PRODUCTS: Record<string, string> = {
  nakitce_premium_monthly: "aylık",
  nakitce_premium_yearly: "yıllık",
};
const CONSENT_KINDS = new Set(["privacy", "terms", "ocr_upload", "marketing"]);

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

function daysLeft(endsAt: string | null | undefined): number {
  if (!endsAt) return 0;
  return Math.max(0, Math.ceil((new Date(endsAt).getTime() - Date.now()) / DAY));
}

// deno-lint-ignore no-explicit-any
type Row = Record<string, any>;

function entitlement(row: Row | null) {
  const now = Date.now();
  const plan = String(row?.plan ?? "basic");
  const trialEnds = row?.trial_ends_at ? new Date(row.trial_ends_at).getTime() : 0;
  const premiumEnds = row?.premium_ends_at ? new Date(row.premium_ends_at).getTime() : 0;
  const trialActive = plan === "trial" && trialEnds > now;
  const paidActive = plan === "premium" && (premiumEnds === 0 || premiumEnds > now);
  const premium_active = Boolean(row?.premium_active) && (trialActive || paidActive);
  const endsAt = plan === "trial" ? row?.trial_ends_at : row?.premium_ends_at;

  return {
    server_verified: true as const,
    plan: premium_active ? plan : "basic",
    premium_active,
    source: row?.source ?? null,
    auto_renewing: Boolean(row?.auto_renewing),
    trial_days_left: trialActive ? daysLeft(row?.trial_ends_at) : 0,
    premium_days_left: paidActive ? daysLeft(row?.premium_ends_at) : 0,
    trial_started_at: row?.trial_started_at ?? null,
    trial_ends_at: row?.trial_ends_at ?? null,
    premium_ends_at: row?.premium_ends_at ?? null,
    ends_at: premium_active ? endsAt ?? null : null,
    play_product_id: row?.play_product_id ?? null,
    play_status: row?.play_status ?? null,
    message: premium_active
      ? trialActive
        ? "Premium denemesi sunucu saatiyle etkin."
        : "Premium üyelik sunucuda doğrulandı."
      : "Temel üyelik.",
  };
}

// ---------------------------------------------------------------- Google Play

function b64url(input: ArrayBuffer | string): string {
  const bytes = typeof input === "string"
    ? new TextEncoder().encode(input)
    : new Uint8Array(input);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function googleAccessToken(): Promise<string | null> {
  const raw = Deno.env.get("GOOGLE_SERVICE_ACCOUNT_JSON");
  if (!raw) return null;
  const account = JSON.parse(raw);
  const header = b64url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const iat = Math.floor(Date.now() / 1000);
  const claim = b64url(JSON.stringify({
    iss: account.client_email,
    scope: "https://www.googleapis.com/auth/androidpublisher",
    aud: "https://oauth2.googleapis.com/token",
    iat,
    exp: iat + 3000,
  }));
  const pem = String(account.private_key)
    .replace(/-----[A-Z ]+-----/g, "")
    .replace(/\s+/g, "");
  const der = Uint8Array.from(atob(pem), (c) => c.charCodeAt(0));
  const key = await crypto.subtle.importKey(
    "pkcs8",
    der,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    key,
    new TextEncoder().encode(`${header}.${claim}`),
  );
  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: `${header}.${claim}.${b64url(signature)}`,
    }),
  });
  if (!response.ok) throw new Error("Google yetkilendirmesi başarısız.");
  return (await response.json()).access_token as string;
}

type PlayResult = {
  active: boolean;
  state: string;
  productId: string;
  expiry: string | null;
  autoRenewing: boolean;
  orderId: string | null;
  acknowledged: boolean;
  accountId: string | null;
};

async function queryPlay(token: string): Promise<PlayResult | null> {
  const access = await googleAccessToken();
  if (!access) return null;
  const pkg = Deno.env.get("PLAY_PACKAGE_NAME") ?? "com.mirasteknoloji.nakitce";
  const response = await fetch(
    `https://androidpublisher.googleapis.com/androidpublisher/v3/applications/${pkg}/purchases/subscriptionsv2/tokens/${encodeURIComponent(token)}`,
    { headers: { Authorization: `Bearer ${access}` } },
  );
  if (response.status === 404 || response.status === 410 || response.status === 400) {
    return { active: false, state: "NOT_FOUND", productId: "", expiry: null, autoRenewing: false, orderId: null, acknowledged: false, accountId: null };
  }
  if (!response.ok) throw new Error("Google Play yanıt vermedi.");
  const data = await response.json();
  const item = (data.lineItems ?? [])[0] ?? {};
  const expiry: string | null = item.expiryTime ?? null;
  const state = String(data.subscriptionState ?? "");
  const stillValid = expiry ? new Date(expiry).getTime() > Date.now() : false;
  const entitled = state === "SUBSCRIPTION_STATE_ACTIVE" ||
    state === "SUBSCRIPTION_STATE_IN_GRACE_PERIOD" ||
    (state === "SUBSCRIPTION_STATE_CANCELED" && stillValid);
  return {
    active: entitled && stillValid,
    state,
    productId: String(item.productId ?? ""),
    expiry,
    autoRenewing: Boolean(item.autoRenewingPlan?.autoRenewEnabled),
    orderId: data.latestOrderId ?? null,
    acknowledged: data.acknowledgementState === "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
    accountId: data.externalAccountIdentifiers?.obfuscatedExternalAccountId ?? null,
  };
}

async function acknowledgePlay(productId: string, token: string) {
  const access = await googleAccessToken();
  if (!access) return;
  const pkg = Deno.env.get("PLAY_PACKAGE_NAME") ?? "com.mirasteknoloji.nakitce";
  await fetch(
    `https://androidpublisher.googleapis.com/androidpublisher/v3/applications/${pkg}/purchases/subscriptions/${productId}/tokens/${encodeURIComponent(token)}:acknowledge`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${access}`, "Content-Type": "application/json" },
      body: "{}",
    },
  );
}

// ---------------------------------------------------------------------- main

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });

  try {
    const authHeader = req.headers.get("Authorization") ?? "";
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    const anonKey = Deno.env.get("SUPABASE_ANON_KEY") ?? "";

    if (!supabaseUrl || !serviceKey) {
      return json({ error: "Sunucu yapılandırması eksik." }, 500);
    }

    const userClient = createClient(supabaseUrl, anonKey || serviceKey, {
      global: { headers: { Authorization: authHeader } },
    });
    const { data: { user }, error: userError } = await userClient.auth.getUser();
    if (userError || !user) return json({ error: "Oturum gerekli." }, 401);

    const admin = createClient(supabaseUrl, serviceKey);
    const body = await req.json().catch(() => ({}));
    const action = body?.action ?? "status";

    const log = (kind: string, detail: Row = {}) =>
      admin.from("subscription_events").insert({ user_id: user.id, kind, detail });

    const loadRow = async (): Promise<Row | null> => {
      const { data } = await admin.from("memberships").select("*")
        .eq("user_id", user.id).maybeSingle();
      return data;
    };

    // --------------------------------------------------------------- status
    if (action === "status") {
      let row = await loadRow();
      const emailConfirmed = Boolean(user.email_confirmed_at);

      if (!row) {
        const trialStart = emailConfirmed ? new Date() : null;
        const trialEnd = trialStart ? new Date(trialStart.getTime() + TRIAL_DAYS * DAY) : null;
        const { data: created, error } = await admin.from("memberships").insert({
          user_id: user.id,
          email: user.email,
          plan: emailConfirmed ? "trial" : "basic",
          source: emailConfirmed ? "trial" : null,
          trial_started_at: trialStart?.toISOString() ?? null,
          trial_ends_at: trialEnd?.toISOString() ?? null,
          premium_active: emailConfirmed,
          email_verified_at: user.email_confirmed_at ?? null,
        }).select("*").single();
        if (error) return json({ error: error.message }, 400);
        row = created;
      } else if (
        emailConfirmed && !row.trial_started_at && row.plan === "basic" &&
        !row.play_purchase_token
      ) {
        const trialStart = new Date();
        const { data: updated, error } = await admin.from("memberships").update({
          plan: "trial",
          source: "trial",
          trial_started_at: trialStart.toISOString(),
          trial_ends_at: new Date(trialStart.getTime() + TRIAL_DAYS * DAY).toISOString(),
          premium_active: true,
          email_verified_at: user.email_confirmed_at,
          email: user.email,
        }).eq("user_id", user.id).select("*").single();
        if (error) return json({ error: error.message }, 400);
        row = updated;
      } else if (
        row.source === "play" && row.play_purchase_token &&
        (!row.premium_ends_at || new Date(row.premium_ends_at).getTime() < Date.now() + DAY)
      ) {
        // Yenileme / iptal / iade: süre dolmak üzereyse Google'dan tazele.
        try {
          const play = await queryPlay(row.play_purchase_token);
          if (play) {
            const { data: updated } = await admin.from("memberships").update({
              plan: play.active ? "premium" : "basic",
              premium_active: play.active,
              premium_ends_at: play.expiry,
              auto_renewing: play.autoRenewing,
              play_status: play.state,
              last_verified_at: new Date().toISOString(),
            }).eq("user_id", user.id).select("*").single();
            row = updated ?? row;
          }
        } catch (error) {
          console.error("play refresh", String(error));
        }
      }

      const live = entitlement(row);
      if (row?.premium_active && !live.premium_active) {
        const { data: updated } = await admin.from("memberships")
          .update({ plan: "basic", premium_active: false })
          .eq("user_id", user.id).select("*").single();
        row = updated ?? row;
      }
      return json(entitlement(row));
    }

    // --------------------------------------------------------- redeem_code
    if (action === "redeem_code") {
      const code = String(body?.code ?? "").toUpperCase().replace(/[^A-Z0-9]/g, "");
      if (code.length !== 12) {
        return json({ error: "Kod 12 karakterli olmalı (örn. ABCD-EFGH-JKLM)." }, 400);
      }
      const formatted = `${code.slice(0, 4)}-${code.slice(4, 8)}-${code.slice(8)}`;

      const since = new Date(Date.now() - 3_600_000).toISOString();
      const { count: failures } = await admin.from("subscription_events")
        .select("id", { count: "exact", head: true })
        .eq("user_id", user.id).eq("kind", "redeem_failed").gte("created_at", since);
      if ((failures ?? 0) >= 8) {
        return json({ error: "Çok fazla hatalı deneme. Bir saat sonra tekrar dene." }, 429);
      }

      const nowIso = new Date().toISOString();
      const { data: claimed } = await admin.from("activation_codes")
        .update({ used_by: user.id, used_at: nowIso })
        .eq("code", formatted).is("used_by", null)
        .or(`expires_at.is.null,expires_at.gt.${nowIso}`)
        .select("code, days").maybeSingle();
      if (!claimed) {
        await log("redeem_failed", { code_tail: formatted.slice(-4) });
        return json({ error: "Kod geçersiz, süresi dolmuş veya daha önce kullanılmış." }, 400);
      }

      const row = await loadRow();
      const base = row?.plan === "premium" && row?.premium_ends_at &&
          new Date(row.premium_ends_at).getTime() > Date.now()
        ? new Date(row.premium_ends_at).getTime()
        : Date.now();
      const ends = new Date(base + Number(claimed.days) * DAY).toISOString();
      const { data: updated, error } = await admin.from("memberships").upsert({
        user_id: user.id,
        email: user.email,
        plan: "premium",
        source: "code",
        premium_active: true,
        premium_ends_at: ends,
        email_verified_at: user.email_confirmed_at ?? null,
      }, { onConflict: "user_id" }).select("*").single();
      if (error) return json({ error: error.message }, 400);
      await log("redeem_ok", { code_tail: formatted.slice(-4), days: claimed.days });
      return json({
        ...entitlement(updated),
        message: `Kod uygulandı: ${claimed.days} gün Premium eklendi.`,
      });
    }

    // ------------------------------------------------ verify_play_purchase
    if (action === "verify_play_purchase") {
      const token = String(body?.purchase_token ?? "");
      const productId = String(body?.product_id ?? "");
      if (!token) return json({ error: "purchase_token gerekli." }, 400);
      if (productId && !(productId in PRODUCTS)) {
        return json({ error: "Ürün kimliği Play kataloğuyla eşleşmiyor." }, 400);
      }
      if (!Deno.env.get("GOOGLE_SERVICE_ACCOUNT_JSON")) {
        return json({
          error: "Google Play doğrulaması sunucuda yapılandırılmadı.",
          server_verified: false,
        }, 501);
      }

      const { data: owner } = await admin.from("memberships")
        .select("user_id").eq("play_purchase_token", token).maybeSingle();
      if (owner && owner.user_id !== user.id) {
        await log("play_token_conflict");
        return json({ error: "Bu satın alma başka bir hesaba bağlı." }, 409);
      }

      const play = await queryPlay(token);
      if (!play || !play.active) {
        await log("play_rejected", { state: play?.state ?? "unknown" });
        return json({ error: "Satın alma geçerli bir abonelik göstermiyor.", server_verified: false }, 400);
      }
      if (!(play.productId in PRODUCTS)) {
        return json({ error: "Ürün kimliği Play kataloğuyla eşleşmiyor." }, 400);
      }
      if (play.accountId && play.accountId !== user.id) {
        await log("play_account_mismatch");
        return json({ error: "Bu satın alma başka bir hesap için yapılmış." }, 409);
      }

      const { data: updated, error } = await admin.from("memberships").upsert({
        user_id: user.id,
        email: user.email,
        plan: "premium",
        source: "play",
        premium_active: true,
        premium_ends_at: play.expiry,
        auto_renewing: play.autoRenewing,
        play_product_id: play.productId,
        play_purchase_token: token,
        play_order_id: play.orderId,
        play_status: play.state,
        last_verified_at: new Date().toISOString(),
        email_verified_at: user.email_confirmed_at ?? null,
      }, { onConflict: "user_id" }).select("*").single();
      if (error) return json({ error: error.message }, 400);
      if (!play.acknowledged) await acknowledgePlay(play.productId, token);
      await log("play_verified", { product: play.productId, order: play.orderId });
      return json({
        ...entitlement(updated),
        message: "Google Play aboneliği doğrulandı.",
      });
    }

    // ------------------------------------------------------ record_consent
    if (action === "record_consent") {
      const kind = String(body?.kind ?? "");
      if (!CONSENT_KINDS.has(kind)) return json({ error: "Geçersiz rıza türü." }, 400);
      const { error } = await admin.from("app_consents").insert({
        user_id: user.id,
        kind,
        version: String(body?.version ?? "1").slice(0, 32),
        accepted: body?.accepted !== false,
      });
      if (error) return json({ error: error.message }, 400);
      return json({ ok: true });
    }

    // ------------------------------------------------------ delete_account
    if (action === "delete_account") {
      if (body?.confirm !== "SIL") return json({ error: "Silme onayı gerekli." }, 400);
      await log("account_deleted", {});
      const { error } = await admin.auth.admin.deleteUser(user.id);
      if (error) return json({ error: error.message }, 400);
      return json({ ok: true, message: "Hesap ve bulut verileri silindi." });
    }

    return json({ error: "Bilinmeyen action." }, 400);
  } catch (error) {
    console.error(String(error));
    return json({ error: "Sunucu hatası. Biraz sonra tekrar dene." }, 500);
  }
});
