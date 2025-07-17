# main.py
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="Tempest Wash Co Cleaning Services",
    description="Professional cleaning services for homes and businesses",
    version="1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add global template variables
templates.env.globals["current_year"] = datetime.now().year

# Services database
SERVICES = [
    {"id": "residential", "title": "Residential Pressure Washing", "icon": "fa-home",
     "description": "Driveways, patios, sidewalks, fences, siding. We clean it all with care and precision."},
    {"id": "commercial", "title": "Commercial Pressure Washing ", "icon": "fa-building",
     "description": "Storefronts, parking lots, warehouses, signage, and heavy-traffic concrete areas, spotless and professional."},
    {"id": "deep", "title": "Soft Washing", "icon": "fa-broom",
     "description": "Safe and effective cleaning for roofs, stucco, painted wood, and delicate surfaces."},
    {"id": "window", "title": "Window Cleaning", "icon": "fa-window-restore",
     "description": "Crystal-clear, streak-free window cleaning  interior and exterior."},
]

# Testimonials
TESTIMONIALS = [
    {"name": "Sarah Johnson", "rating": 5,
     "text": "Tempest Wash Co did an amazing job on my driveway and patio. Their team was professional, punctual, and used eco-friendly products, which I really appreciate.",
     "image": "tempestwashco.jpg"},
    {"name": "Michael Rodriguez", "rating": 5,
     "text": "Highly recommend for anyone needing pressure washing in LA!",
     "image": "tempestwashco.jpg"},
    {"name": "Emma Thompson", "rating": 5,
     "text": "Excellent service from start to finish! The team at Tempest Wash Co was thorough and careful with my home’s exterior. I love that they use environmentally safe cleaning solutions. My house looks spotless!",
     "image": "tempestwashco.jpg"},
]


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": SERVICES[:4],
        "testimonials": TESTIMONIALS
    })


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about_us.html", {"request": request})


@app.get("/services", response_class=HTMLResponse)
async def services(request: Request):
    return templates.TemplateResponse("services.html", {
        "request": request,
        "services": SERVICES
    })


@app.get("/services/residential", response_class=HTMLResponse)
async def services_residential(request: Request):
    return templates.TemplateResponse("residential.html", {"request": request})


@app.get("/services/commercial", response_class=HTMLResponse)
async def services_commercial(request: Request):
    return templates.TemplateResponse("commercial.html", {"request": request})


@app.get("/services/window-cleaning", response_class=HTMLResponse)
async def services_window_cleaning(request: Request):
    return templates.TemplateResponse("window-cleaning.html", {"request": request})


# @app.get("/contact", response_class=HTMLResponse)
# async def contact(request: Request):
#     return templates.TemplateResponse("contact.html", {"request": request})


# 404 Error Handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.middleware("http")
async def redirect_to_www(request: Request, call_next):
    host = request.headers.get("host", "")
    if host == "tempestwashco.com":
        url = request.url.replace(netloc="www.tempestwashco.com")
        return RedirectResponse(url=str(url), status_code=301)
    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
