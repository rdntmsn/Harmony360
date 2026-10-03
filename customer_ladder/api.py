from fastapi import FastAPI

from .models import Blueprint, CustomerIntake
from .service import build_blueprint

app = FastAPI(
    title="Harmony360 Customer Ladder API",
    version="0.1.0",
    description="Signal-to-System intake, blueprinting, and offer qualification.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "harmony360-customer-ladder"}


@app.post("/blueprint", response_model=Blueprint)
def create_blueprint(intake: CustomerIntake) -> Blueprint:
    return build_blueprint(intake)
