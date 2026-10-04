from pydantic import BaseModel, Field


class LocationSuggestion(BaseModel):
    """A privacy-safe place result selected explicitly by the user."""

    name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
