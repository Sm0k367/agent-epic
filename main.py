from fastapi import FastAPI
from typing import Dict

# Initialize the main FastAPI application
app = FastAPI(
    title="ETAI-X Prime - Hyper-Accelerated Digital Ecosystem",
    description="The central API gateway for the AI Entertainment &amp; Social Platform.",
    version="1.0.0",
)

# --- API Routers ---
# Placeholder for including routers from other modules
from .routers import social, content, experience, agent

app.include_router(social.router, prefix="/social", tags=["Social Platform"])
app.include_router(content.router, prefix="/content", tags=["AI Content Engine"])
app.include_router(experience.router, prefix="/experience", tags=["Multi-Modal Experiences"])
app.include_router(agent.router, prefix="/agent", tags=["Specialized Agent"])
# app.include_router(content.router, prefix="/content", tags=["AI Content Engine"])
# app.include_router(experience.router, prefix="/experience", tags=["Multi-Modal Experiences"])
# ---

@app.get("/", tags=["Root"])
async def read_root() -> Dict[str, str]:
    """
    Root endpoint to confirm the API is operational.
    """
    return {"message": "ETAI-X Prime API is online and operational."}

# To run this application:
# 1. Navigate to the `platform` directory in your terminal.
# 2. Activate the virtual environment: source venv/bin/activate
# 3. Run the server: uvicorn backend.main:app --reload