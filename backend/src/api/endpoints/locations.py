import unicodedata
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query, status

from src.api.dependencies import CurrentUser
from src.models.location import LocationSuggestion


router = APIRouter(prefix="/locations", tags=["Locations"])

# The browser only sends coordinates after the user explicitly grants location
# permission. Photon is called server-side so neither an API key nor a user's
# precise coordinates are exposed to a third-party script in the browser.
_PHOTON_URL = "https://photon.komoot.io"
_HEADERS = {"User-Agent": "HVNH-Hub/1.0 contact: admin@hvnh.edu.vn"}
_VIETNAM_BBOX = "102.14,8.18,109.47,23.39"


def _normalize_query(value: str) -> str:
    """Photon's public index is much more reliable for Vietnamese when queried without accents."""
    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return normalized.replace("đ", "d").replace("Đ", "D")


def _suggestion(feature: dict) -> LocationSuggestion:
    properties = feature.get("properties") or {}
    coordinates = (feature.get("geometry") or {}).get("coordinates") or []
    if len(coordinates) < 2:
        raise ValueError("Missing Photon coordinates")
    name = str(properties.get("name") or properties.get("street") or "Vị trí đã chọn").strip()
    address_parts = [
        properties.get("street"), properties.get("locality"), properties.get("district"),
        properties.get("city"), properties.get("state"), properties.get("country"),
    ]
    display_name = ", ".join(dict.fromkeys(str(part).strip() for part in address_parts if part))
    return LocationSuggestion(
        name=name,
        address=display_name or name,
        latitude=float(coordinates[1]),
        longitude=float(coordinates[0]),
    )


async def _photon_get(path: str, params: dict[str, str | int | float]) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=_HEADERS) as client:
            response = await client.get(f"{_PHOTON_URL}{path}", params=params)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tìm địa điểm lúc này. Vui lòng thử lại sau.",
        ) from exc


@router.get("/search", response_model=list[LocationSuggestion])
async def search_locations(
    _: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=5)] = 5,
) -> list[LocationSuggestion]:
    payload = await _photon_get("/api/", {"q": _normalize_query(q.strip()), "limit": limit, "bbox": _VIETNAM_BBOX})
    return [_suggestion(feature) for feature in payload.get("features", []) if (feature.get("geometry") or {}).get("coordinates")]


@router.get("/reverse", response_model=LocationSuggestion | None)
async def reverse_geocode(
    _: CurrentUser,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
) -> LocationSuggestion | None:
    payload = await _photon_get("/reverse", {"lat": latitude, "lon": longitude})
    features = payload.get("features", [])
    if not features:
        return None
    return _suggestion(features[0])
