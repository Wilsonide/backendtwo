from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
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

app = FastAPI(
    title="Country Currency & Exchange API",
    description="Fetch countries, currencies, and exchange rates — and computes estimated GDP values.",
    version="1.0.0",
)

engine = create_engine(config.SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/countries/refresh")
async def refresh_countries(db: Annotated[Session, Depends(get_db)]):
    try:
        countries_data = await utils.fetch_countries()
        exchange_rates = await utils.fetch_exchange_rates()
    except Exception as e:  # noqa: BLE001
        print(f"Error fetching external data: {e}")
        raise HTTPException(  # noqa: B904
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": "Could not fetch data from [API name]",
            },
        )

    saved = []
    for item in countries_data:
        name = item.get("name")
        population = item.get("population")
        capital = item.get("capital")
        region = item.get("region")
        flag = item.get("flag")

        if not name or population is None:
            continue  # skip invalid

        currency_code = utils.extract_currency_code(item)
        if currency_code is None:
            exchange_rate = None
            estimated_gdp = 0
        else:
            exchange_rate = exchange_rates.get(currency_code)
            if exchange_rate is None:
                estimated_gdp = None
            else:
                estimated_gdp = utils.compute_estimated_gdp(population, exchange_rate)

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
        }

        obj = crud.create_or_update_country(db, payload)
        saved.append(obj)

    # ensure image uses the db-saved objects (which contain last_refreshed_at)
    image.generate_summary_image(saved)
    return {"message": "Countries refreshed successfully", "total": len(saved)}


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
    # image saved under package app/cache/summary.png
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=config.PORT)
