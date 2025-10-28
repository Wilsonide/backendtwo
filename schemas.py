from datetime import datetime

from pydantic import BaseModel, Field


class CountryBase(BaseModel):
    name: str = Field(..., min_length=1)
    capital: str | None = None
    region: str | None = None
    population: int = Field(..., ge=0)
    currency_code: str | None = None


class CountryCreate(CountryBase):
    exchange_rate: float | None = None
    estimated_gdp: float | None = None
    flag_url: str | None = None


class CountryResponse(CountryBase):
    id: int
    exchange_rate: float | None = None
    estimated_gdp: float | None = None
    flag_url: str | None = None
    last_refreshed_at: datetime | None = None

    class Config:
        orm_mode = True
        # Format datetime output like "2025-10-28T03:30:00Z"
        json_encoders = {  # noqa: RUF012
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M:%SZ") if v else None,
        }
