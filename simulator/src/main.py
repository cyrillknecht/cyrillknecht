from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from src.api.routes import router, scenario_router
from src.scenario.engine import ScenarioEngine
import os

app = FastAPI(
    title="ISR Data Source Simulator",
    description="Simulated UAV, satellite, HUMINT, NATO intel, and civilian data feeds over Switzerland.",
    version="2.0.0",
)

app.include_router(router, prefix="/sources")
app.include_router(scenario_router, prefix="/scenario")

_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.on_event("startup")
def startup():
    ScenarioEngine.get()


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/map", include_in_schema=False)
def cop_map():
    return RedirectResponse(url="/static/index.html")
