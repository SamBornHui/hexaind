from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel


from databrick.demo_optimization_api.demos import cone_areas, can_fem, ai_physics, bced_v1, bced_v2

class Recommendations(BaseModel):
    recommendation: Dict[str, float]
    demo_name: str

demo_functions = {
            "demo_1": cone_areas,
            "can_fem": can_fem,
            "ai_physics": ai_physics,
            "bced_v1": bced_v1,
            "bced_v2": bced_v2
        }


app = FastAPI()

# @app.get("/", status_code=200)
@app.get("/hexaindanalytics/mobo/", status_code=200)
async def root():
    return {"detail": "This is the demo API for Hexaind optimization functions (MOBO)."}

# @app.post("/recommendations/")
@app.post("/hexaindanalytics/mobo/recommendations/")
async def update_recommendations(recommendations: Recommendations):
    demo_function = demo_functions[recommendations.demo_name]
    new_vals = demo_function(recommendations.recommendation)
    return new_vals

# @app.post("/can-end-fem/")
@app.post("/hexaindanalytics/mobo/can-end-fem/")
async def update_can_fem(recommendations: Recommendations):
    demo_function = demo_functions[recommendations.demo_name]
    new_vals = demo_function(recommendations.recommendation)
    return new_vals

@app.post("/hexaindanalytics/mobo/bced_v1/")
async def update_bced_v1(recommendations: Recommendations):
    demo_function = demo_functions[recommendations.demo_name]
    new_vals = demo_function(recommendations.recommendation)
    return new_vals

@app.post("/hexaindanalytics/mobo/bced_v2/")
async def update_bced(recommendations: Recommendations):
    demo_function = demo_functions[recommendations.demo_name]
    new_vals = demo_function(recommendations.recommendation)
    return new_vals

@app.post("/x1/")
@app.post("/hexaindanalytics/mobo/x1/")
async def x1_times_2(x1: int):
    return x1 * 2

@app.post("/hexaindanalytics/mobo/ai_physics/")
async def update_ai_physics(recommendations: Recommendations):
    demo_function = demo_functions[recommendations.demo_name]
    new_vals = demo_function(recommendations.recommendation)
    return new_vals

