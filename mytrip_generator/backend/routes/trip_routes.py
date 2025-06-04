from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..models.itinerary import TripRequest
from ..agents.itinerary_builder import build_itinerary
import os

router = APIRouter()

@router.post("/api/trip")
async def generate_itinerary(trip: TripRequest):
    try:
        result = build_itinerary(trip.dict())
        return {
            "itinerary": result["itinerary"],
            "vibe": result["vibe"],
            "pdf_path": os.path.basename(result["pdf_path"]) if result["pdf_path"] else "",
            "error": result["itinerary"] if result["itinerary"].startswith("Error") else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating itinerary: {str(e)}")

@router.get("/api/download_pdf/{filename}")
async def download_pdf(filename: str):
    file_path = os.path.join("output/static", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    raise HTTPException(status_code=404, detail="PDF file not found")