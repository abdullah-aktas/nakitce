"""Flet-compatible Google Play Billing bridge (stub until product IDs exist).

The Android native side should expose purchase tokens to Python. Never put
Google service-account keys or Supabase service_role in the Flet app.
"""

import logging

log = logging.getLogger("app.billing_bridge")

# Draft SKUs — replace with Play Console product IDs when created.
PRODUCT_MONTHLY = "nakitce_premium_monthly"
PRODUCT_YEARLY = "nakitce_premium_yearly"


class BillingBridge:
    """Thin adapter; returns None until a native Play Billing channel is wired."""

    def __init__(self, page=None):
        self.page = page
        self.available = False

    async def query_products(self):
        """Return localized product info from Play when the bridge is live."""
        return []

    async def launch_purchase(self, product_id):
        """Start a Play Billing purchase flow. Returns purchase_token or None."""
        log.info("Play Billing bridge not configured; purchase skipped for %s", product_id)
        return None

    async def restore_purchases(self):
        """Return existing purchase tokens for server verification."""
        return []
