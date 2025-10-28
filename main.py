import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import config
import crud
import image
import models
import schemas
import utils
from crud import create_or_update_country

app = FastAPI(
    title="Country Currency & Exchange API",
    description="Fetch countries, currencies, and exchange rates — and computes estimated GDP values.",
    version="1.0.0",
)

print(config.SQLALCHEMY_DATABASE_URL)

# ✅ Database setup
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    connect_args={"ssl": {"ssl_mode": "REQUIRED"}},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
models.Base.metadata.create_all(bind=engine)

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Background task function
def background_refresh_countries():
    """Runs the refresh operation in the background."""
    db = SessionLocal()

    try:
        print("⏳ [Background] Fetching countries and exchange rates...")
        countries_data = asyncio.run(utils.fetch_countries())
        exchange_rates = asyncio.run(utils.fetch_exchange_rates())
        print(f"✅ [Background] Retrieved {len(countries_data)} countries.")

        saved = []
        for item in countries_data:
            name = item.get("name")
            population = item.get("population")
            capital = item.get("capital")
            region = item.get("region")
            flag = item.get("flag")

            if not name or population is None:
                continue

            currency_code = utils.extract_currency_code(item)
            if currency_code is None:
                exchange_rate = None
                estimated_gdp = 0
            else:
                exchange_rate = exchange_rates.get(currency_code)
                estimated_gdp = (
                    utils.compute_estimated_gdp(population, exchange_rate)
                    if exchange_rate is not None
                    else None
                )

            payload = {
                "name": name,
                "capital": capital,
                "region": region,
                "population": int(population),
                "currency_code": currency_code,
                "exchange_rate": float(exchange_rate)
                if exchange_rate is not None
                else None,
                "estimated_gdp": float(estimated_gdp)
                if estimated_gdp is not None
                else None,
                "flag_url": flag,
                "last_refreshed_at": datetime.now(UTC).strftime(
                    "%Y-%m-%d %H:%M:%S UTC",
                ),
            }

            obj = create_or_update_country(db, payload)
            saved.append(obj)

        db.commit()
        image.generate_summary_image(saved)
        print(f"✅ [Background] Refresh completed — {len(saved)} countries updated.")
    except Exception as e:
        print(f"❌ [Background] Refresh failed: {e}")
    finally:
        db.close()


# ✅ Non-blocking route
@app.post("/countries/refresh")
async def refresh_countries(background_tasks: BackgroundTasks):
    """Trigger a background refresh of countries and exchange rates."""
    background_tasks.add_task(background_refresh_countries)
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"🚀 Refresh job started in background at {now}")

    return {
        "message": "Background refresh started",
        "started_at": now,
        "note": "Processing in background — check /countries/image or /status later.",
    }


# ✅ CRUD routes
@app.get("/countries", response_model=list[schemas.CountryResponse])
def get_countries(
    db: Annotated[Session, Depends(get_db)],
    region: str | None = None,
    currency: str | None = None,
    sort: str | None = None,
):
    return crud.get_countries(db, region, currency, sort)


@app.get("/countries/image")
def get_image():
    path = Path(__file__).resolve().parent / "cache" / "summary.png"
    if not path.exists():
        raise HTTPException(404, detail={"error": "Summary image not found"})
    return FileResponse(path, media_type="image/png")


@app.get("/countries/{name}", response_model=schemas.CountryResponse)
def get_country(name: str, db: Annotated[Session, Depends(get_db)]):
    country = crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(404, detail={"error": "Country not found"})
    return country


@app.delete("/countries/{name}")
def delete_country(name: str, db: Annotated[Session, Depends(get_db)]):
    country = crud.delete_country(db, name)
    if not country:
        raise HTTPException(404, detail={"error": "Country not found"})
    return {"message": f"{name} deleted successfully"}


@app.get("/status")
def status(db: Annotated[Session, Depends(get_db)]):
    return crud.get_status(db)


# ✅ Run app
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=config.PORT)
