from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any website to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
