"""Configuração central do backend (caminhos e limites)."""

from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[2]  # pdi_project/
CATALOG_PATH = Path(os.getenv("PDI_CATALOG_PATH", ROOT_DIR / "shared" / "processes.json"))
FRONTEND_DIST = Path(os.getenv("PDI_FRONTEND_DIST", ROOT_DIR / "frontend" / "dist"))
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_IMAGE_SIDE = 4096
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
DETECTION_IMAGE_SIZE = 8
