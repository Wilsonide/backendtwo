import random

import httpx

COUNTRIES_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_API = "https://open.er-api.com/v6/latest/USD"


def compute_estimated_gdp(population: int, exchange_rate: float | None) -> float | None:
    if exchange_rate is None:
        return None
    multiplier = random.randint(1000, 2000)
    return (population * multiplier) / exchange_rate


def extract_currency_code(country_item: dict) -> str | None:
    currs = country_item.get("currencies")
    if not currs or not isinstance(currs, list) or len(currs) == 0:
        return None
    first = currs[0]
    return first.get("code")


async def fetch_countries() -> list[dict]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(COUNTRIES_API)
        r.raise_for_status()
        return r.json()


async def fetch_exchange_rates() -> dict[str, float]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(EXCHANGE_API)
        r.raise_for_status()
        data = r.json()
        rates = data.get("rates") or {}
        return rates
