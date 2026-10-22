// Nakitçe membership Edge Function (Deno / Supabase)
// Deploy on the Miras Teknoloji membership project only.
// Secrets: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
// Optional later: GOOGLE_PLAY_SERVICE_ACCOUNT_JSON, PLAY_PACKAGE_NAME
//
// Client actions: { action: "status" } | { action: "verify_play_purchase", purchase_token, product_id? }

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.1";

const TRIAL_DAYS = 30;
const DRAFT_PRODUCTS = new Set([
  "nakitce_premium_monthly",
  "nakitce_premium_yearly",
]);

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

function daysLeft(endsAt: string | null): number {
  if (!endsAt) return 0;
  const ms = new Date(endsAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / (24 * 60 * 60 * 1000)));
}

function entitlement(row: Record<string, unknown> | null) {
  const now = Date.now();
  const plan = String(row?.plan ?? "basic");
  const trialEnds = row?.trial_ends_at ? new Date(String(row.trial_ends_at)).getTime() : 0;
  const premiumEnds = row?.premium_ends_at
    ? new Date(String(row.premium_ends_at)).getTime()
    : 0;
  const trialActive = plan === "trial" && trialEnds > now;
  const paidActive = plan === "premium" && (premiumEnds === 0 || premiumEnds > now);
  const premium_active = Boolean(row?.premium_active) && (trialActive || paidActive);
  return {
    server_verified: true as const,
    plan: premium_active ? plan : "basic",
    premium_active,
    trial_days_left: trialActive ? daysLeft(String(row?.trial_ends_at)) : 0,
    trial_started_at: row?.trial_started_at ?? null,
    trial_ends_at: row?.trial_ends_at ?? null,
    premium_ends_at: row?.premium_ends_at ?? null,
    play_product_id: row?.play_product_id ?? null,
    play_status: row?.play_status ?? null,
    message: premium_active
      ? trialActive
        ? "Premium denemesi sunucu saatiyle etkin."
        : "Premium abonelik sunucuda doğrulandı."
      : "Temel üyelik.",
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: cors });
  }
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
    const {
      data: { user },
      error: userError,
    } = await userClient.auth.getUser();
    if (userError || !user) {
      return json({ error: "Oturum gerekli." }, 401);
    }

    const admin = createClient(supabaseUrl, serviceKey);
    const body = await req.json().catch(() => ({}));
    const action = body?.action ?? "status";

    if (action === "status") {
      const { data: existing } = await admin
        .from("memberships")
        .select("*")
        .eq("user_id", user.id)
        .maybeSingle();

      let row = existing;
      const emailConfirmed = Boolean(user.email_confirmed_at);
      if (!row) {
        const trialStart = emailConfirmed ? new Date() : null;
        const trialEnd = trialStart
          ? new Date(trialStart.getTime() + TRIAL_DAYS * 24 * 60 * 60 * 1000)
          : null;
        const insert = {
          user_id: user.id,
          email: user.email,
          plan: emailConfirmed ? "trial" : "basic",
          trial_started_at: trialStart?.toISOString() ?? null,
          trial_ends_at: trialEnd?.toISOString() ?? null,
          premium_active: emailConfirmed,
          email_verified_at: user.email_confirmed_at ?? null,
        };
        const { data: created, error } = await admin
          .from("memberships")
          .insert(insert)
          .select("*")
          .single();
        if (error) return json({ error: error.message }, 400);
        row = created;
      } else if (
        emailConfirmed &&
        !row.trial_started_at &&
        row.plan === "basic" &&
        !row.play_purchase_token
      ) {
        // Start trial once on first verified email — server clock only.
        const trialStart = new Date();
        const trialEnd = new Date(
          trialStart.getTime() + TRIAL_DAYS * 24 * 60 * 60 * 1000,
        );
        const { data: updated, error } = await admin
          .from("memberships")
          .update({
            plan: "trial",
            trial_started_at: trialStart.toISOString(),
            trial_ends_at: trialEnd.toISOString(),
            premium_active: true,
            email_verified_at: user.email_confirmed_at,
            email: user.email,
          })
          .eq("user_id", user.id)
          .select("*")
          .single();
        if (error) return json({ error: error.message }, 400);
        row = updated;
      } else {
        // Expire stale trial/premium using server time.
        const live = entitlement(row);
        if (row.premium_active && !live.premium_active) {
          const { data: updated } = await admin
            .from("memberships")
            .update({ plan: "basic", premium_active: false })
            .eq("user_id", user.id)
            .select("*")
            .single();
          row = updated ?? row;
        }
      }
      return json(entitlement(row));
    }

    if (action === "verify_play_purchase") {
      const token = String(body?.purchase_token ?? "");
      const productId = String(body?.product_id ?? "");
      if (!token) return json({ error: "purchase_token gerekli." }, 400);
      if (productId && !DRAFT_PRODUCTS.has(productId)) {
        return json({
          error:
            "Ürün kimliği henüz Play Console ile eşleşmiyor. Kimlikleri kesinleştirip Edge Function'ı güncelleyin.",
        }, 400);
      }
      // TODO: Call Google Play Developer API with service account.
      // Until wired, reject so the app never trusts a client-only token.
      return json({
        error:
          "Google Play Developer API doğrulaması henüz bağlanmadı. Ürün kimlikleri hazır olunca bu uç noktayı tamamlayın.",
        server_verified: false,
      }, 501);
    }

    return json({ error: "Bilinmeyen action." }, 400);
  } catch (error) {
    return json({ error: String(error) }, 500);
  }
});
