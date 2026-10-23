import uvicorn
from app.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    print(f"Starting AI Resume Analysis & Screening System on http://{HOST}:{PORT}")
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
