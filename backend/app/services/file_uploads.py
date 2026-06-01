from fastapi import HTTPException, UploadFile, status

from app.services.file_parser_service import (
    FileParserError,
    FileParserService,
    SUPPORTED_FILE_EXTENSIONS,
)

SUPPORTED_TEXT_EXTENSIONS = SUPPORTED_FILE_EXTENSIONS


async def read_text_upload(file: UploadFile) -> tuple[str, str]:
    try:
        parsed_file = await FileParserService().parse_upload_file(file)
    except FileParserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return parsed_file.filename, parsed_file.content_text
