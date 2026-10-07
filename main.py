from fastapi import FastAPI
from constants import APP_NAME
from avionica import main as avionica_main
from aircraft import main as aircraft_main
from airport import main as airport_main
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title = APP_NAME,
    summary = "Avionica Manufacture",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(avionica_main.router, prefix="/api")
app.include_router(aircraft_main.router, prefix="/api")
app.include_router(airport_main.router, prefix="/api")