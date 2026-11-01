"""Versioned list-price estimates for provider-reported RAG LLM usage.

Rates are USD per million tokens. Extend PRICE_RULES when switching models;
the matched rule is snapshotted with each usage row so later price changes do
not rewrite historical estimates. This is an estimate, not a provider invoice.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

MILLION = Decimal("1000000")


@dataclass(frozen=True, slots=True)
class PriceRule:
    provider: str
    model_prefix: str
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal
    cached_input_usd_per_million: Decimal | None = None
    source: str = ""
    basis: str = "PAID_STANDARD"


# Rates checked 2026-11-01. Use exact/prefix model matching to support provider
# version strings such as Gemini's returned model_version.
PRICE_RULES = (
    PriceRule("gemini", "gemini-3.5-flash-lite", Decimal("0.30"), Decimal("2.50"),
              Decimal("0.03"), "https://ai.google.dev/gemini-api/docs/pricing"),
    # DeepSeek publishes peak/off-peak and cache-hit rates. This initial generic
    # estimate uses peak rates (conservative); cache-hit rate is also recorded.
    PriceRule("deepseek", "deepseek-flash", Decimal("0.30"), Decimal("1.20"),
              Decimal("0.006"), "https://api-docs.deepseek.com/quick_start/pricing/",
              "PEAK_CONSERVATIVE"),
    PriceRule("deepseek", "deepseek-v4-flash", Decimal("0.30"), Decimal("1.20"),
              Decimal("0.006"), "https://api-docs.deepseek.com/quick_start/pricing/",
              "PEAK_CONSERVATIVE"),
    PriceRule("deepseek", "deepseek-v4-pro", Decimal("1.32"), Decimal("3.96"),
              Decimal("0.044"), "https://api-docs.deepseek.com/quick_start/pricing/",
              "PEAK_CONSERVATIVE"),
)


def estimate_cost(provider: str, model: str, input_tokens: int | None,
                  output_tokens: int | None, cached_input_tokens: int | None = None
                  ) -> tuple[Decimal | None, str]:
    rule = next((item for item in PRICE_RULES
                 if item.provider.casefold() == (provider or "").casefold()
                 and (model or "").casefold().startswith(item.model_prefix.casefold())), None)
    if not rule or input_tokens is None or output_tokens is None:
        return None, "UNPRICED"
    cached = max(0, min(cached_input_tokens or 0, input_tokens))
    uncached = input_tokens - cached
    cache_rate = rule.cached_input_usd_per_million or rule.input_usd_per_million
    total = (Decimal(uncached) * rule.input_usd_per_million
             + Decimal(cached) * cache_rate
             + Decimal(output_tokens) * rule.output_usd_per_million) / MILLION
    return total.quantize(Decimal("0.0000000001"), rounding=ROUND_HALF_UP), rule.basis


def rate_snapshot(provider: str, model: str) -> PriceRule | None:
    return next((item for item in PRICE_RULES
                 if item.provider.casefold() == (provider or "").casefold()
                 and (model or "").casefold().startswith(item.model_prefix.casefold())), None)
