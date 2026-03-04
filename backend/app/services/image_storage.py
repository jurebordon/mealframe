"""Image storage utility for AI meal capture (ADR-013).

Handles resizing, compression, and local volume storage of food photos.
"""
import io
from pathlib import Path
from uuid import UUID

from PIL import Image

from ..config import settings

MAX_DIMENSION = 1920  # pixels
JPEG_QUALITY = 85
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


def save_captured_image(image_bytes: bytes, user_id: UUID, meal_id: UUID) -> str:
    """
    Resize, compress, and save a captured food image to local storage.

    - Resizes to max MAX_DIMENSION on longest side (maintains aspect ratio)
    - Converts to JPEG at JPEG_QUALITY
    - Saves to {captures_dir}/{user_id}/{meal_id}.jpg
    - Creates directories if they don't exist

    Returns:
        Relative path string (e.g., "{user_id}/{meal_id}.jpg")
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA/P to RGB for JPEG compatibility
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Resize if exceeds max dimension
    width, height = img.size
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    # Build storage path
    user_dir = Path(settings.captures_dir) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_dir / f"{meal_id}.jpg"

    img.save(file_path, format="JPEG", quality=JPEG_QUALITY, optimize=True)

    return f"{user_id}/{meal_id}.jpg"


def validate_image_content_type(content_type: str | None) -> bool:
    """Return True if content_type is an accepted image format."""
    return content_type in ALLOWED_CONTENT_TYPES
