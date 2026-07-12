from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import app as auth_app
from tasks import app as tasks_app

app = FastAPI(title="Tasks Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
for route in auth_app.routes:
    app.routes.append(route)
for route in tasks_app.routes:
    app.routes.append(route)