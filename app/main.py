from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Aircraft Maintenance Planner MVP", version="0.1.0")
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "service": "AircraftMaintenancePlanner"}
