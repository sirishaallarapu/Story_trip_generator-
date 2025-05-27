from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from routes.trip_routes import router as trip_router  # import your router here

app = FastAPI()

# Serve static assets like favicon
app.mount("/assets", StaticFiles(directory="../frontend/src/assets"), name="assets")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("../frontend/src/assets/favicon.ico")

@app.get("/")
async def root():
    return {"message": "Welcome to your FastAPI app!"}

# CORS settings to allow frontend at localhost:3000 to access backend
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the trip_routes router that has your /api/generate-itinerary POST endpoint
app.include_router(trip_router)

# Remove the duplicate /api/generate-itinerary here — handled in trip_routes.py
