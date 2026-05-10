from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.document_routes import router as document_router
from routes.chat_routes import router as chat_router

app = FastAPI(title="AI Knowledge Workspace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "AI Knowledge Workspace Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}