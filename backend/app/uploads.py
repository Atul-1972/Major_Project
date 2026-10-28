"""Bounded in-memory multipart parsing and decoded image validation."""

from io import BytesIO
import warnings

from fastapi import HTTPException, Request
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

from .schemas import Quality
from .settings import MAX_IMAGE_BYTES, MAX_REQUEST_BYTES, MAX_PIXELS, MIN_DIMENSION


class MemoryMultipartParser(MultiPartParser):
    # The ASGI middleware caps the entire body below this threshold before parsing.
    # Consequently SpooledTemporaryFile never rolls an accepted request onto disk.
    spool_max_size = MAX_REQUEST_BYTES + 1


async def read_upload(request: Request):
    if request.headers.get('content-type', '').split(';')[0].strip().lower() != 'multipart/form-data':
        raise HTTPException(422, 'A multipart upload with one image field is required.')
    try:
        form = await MemoryMultipartParser(
            request.headers, request.stream(), max_files=1, max_fields=0,
            max_part_size=MAX_IMAGE_BYTES,
        ).parse()
    except (MultiPartException, ValueError):
        raise HTTPException(422, 'Invalid multipart image upload.') from None
    try:
        items = form.multi_items()
        if len(items) != 1 or items[0][0] != 'image' or not isinstance(items[0][1], UploadFile):
            raise HTTPException(422, 'Exactly one image file in the image field is required.')
        data = await items[0][1].read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(413, 'Image exceeds the 10 MiB encoded limit.')
        return data
    finally:
        await form.close()


def decode_image(data: bytes):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in ('JPEG', 'PNG'):
                    raise HTTPException(415, 'Only decoded JPEG and PNG images are supported.')
                image_format = source.format
                width, height = source.size
                if width * height > MAX_PIXELS:
                    raise HTTPException(413, 'Image exceeds the 20 million pixel limit.')
                if min(width, height) < MIN_DIMENSION:
                    raise HTTPException(422, 'Image must be at least 128 pixels in each dimension.')
                if getattr(source, 'n_frames', 1) != 1:
                    raise HTTPException(422, 'Animated or multiframe images are unsupported.')
                source.verify()
            with Image.open(BytesIO(data)) as source:
                image = ImageOps.exif_transpose(source).convert('RGB')
                image.load()
                image.info.clear()
        return image, Quality(format=image_format, width=image.width, height=image.height)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(413, 'Decoded image is too large.') from None
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise HTTPException(422, 'Image is empty, corrupt or unreadable.') from None
