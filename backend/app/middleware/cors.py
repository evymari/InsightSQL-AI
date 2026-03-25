from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app):
    """
    Add CORS middleware to allow frontend connections
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify your frontend domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
