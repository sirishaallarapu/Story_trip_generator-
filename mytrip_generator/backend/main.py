from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.itinerary_builder import build_itinerary
from agents.itinerary_builder import generate_pdf  # import your pdf generation function
import tempfile
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your React app URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class TripInput(BaseModel):
    destination: str
    trip_type: str | None = None
    food_preference: str
    num_members: int
    budget: str
    start_date: str
    end_date: str
    duration: int

@app.post("/api/trip")
async def create_trip(trip_input: TripInput):
    try:
        itinerary = build_itinerary(trip_input.dict())
        if itinerary.startswith("Error:") or itinerary.startswith("No itinerary"):
            raise HTTPException(status_code=400, detail=itinerary)
        return {"itinerary": itinerary, "vibe": itinerary.split("\n")[1], "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint to generate PDF from itinerary
class PDFRequest(BaseModel):
    itinerary: str
    vibe: str | None = None
    destination: str | None = "Your Destination"

@app.post("/api/generate-pdf")
async def generate_pdf_endpoint(data: PDFRequest):
    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        output_path = tmp_file.name

    try:
        success, result = generate_pdf(
            itinerary=data.itinerary,
            output_path=output_path,
            destination=data.destination,
            vibe=data.vibe or ""
        )
        if not success:
            raise HTTPException(status_code=500, detail=result)

        # Read PDF binary content
        with open(output_path, "rb") as f:
            pdf_bytes = f.read()

        # Remove temp file
        os.remove(output_path)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=trip_itinerary.pdf"
            }
        )
    except Exception as e:
        # Ensure temp file cleanup on error
        if os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
