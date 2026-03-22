import uvicorn
import os
from app.main import app
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "0") == "1"

if __name__ == "__main__":
    uvicorn.run("app.main:app",
                host=API_URL,
                port=API_PORT,
                reload=DEBUG,
                log_level="debug")
