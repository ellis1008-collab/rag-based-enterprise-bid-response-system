import pytest

from app.services.file_parser_service import FileParserError, FileParserService
from tests.file_samples import make_blank_pdf, make_docx, make_text_pdf, make_xlsx


def test_parse_pdf_extracts_text() -> None:
    parsed = FileParserService().parse_bytes(
        filename="rfp.pdf",
        raw_content=make_text_pdf("PDF RFP private deployment requirement"),
    )

    assert parsed.extension == ".pdf"
    assert "PDF RFP private deployment requirement" in parsed.content_text


def test_parse_pdf_falls_back_to_ocr_when_text_layer_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    def parse_pdf_with_ocr(self: FileParserService, raw_content: bytes) -> str:
        return "OCR scanned PDF product capability"

    monkeypatch.setattr(FileParserService, "_parse_pdf_with_ocr", parse_pdf_with_ocr)

    parsed = FileParserService().parse_bytes(
        filename="scanned-product.pdf",
        raw_content=make_blank_pdf(),
    )

    assert parsed.extension == ".pdf"
    assert parsed.content_text == "OCR scanned PDF product capability"


def test_parse_docx_extracts_paragraphs_and_tables() -> None:
    parsed = FileParserService().parse_bytes(
        filename="product.docx",
        raw_content=make_docx(
            "DOCX product private deployment capability",
            [["Category", "Capability"], ["Audit", "Operation logs"]],
        ),
    )

    assert parsed.extension == ".docx"
    assert "DOCX product private deployment capability" in parsed.content_text
    assert "Audit\tOperation logs" in parsed.content_text


def test_parse_xlsx_extracts_sheet_name_and_rows() -> None:
    parsed = FileParserService().parse_bytes(
        filename="matrix.xlsx",
        raw_content=make_xlsx(
            "Requirements",
            [["Code", "Requirement"], ["REQ-001", "Support 500 concurrent users"]],
        ),
    )

    assert parsed.extension == ".xlsx"
    assert "Sheet: Requirements" in parsed.content_text
    assert "REQ-001\tSupport 500 concurrent users" in parsed.content_text


def test_parse_rejects_unsupported_file_format() -> None:
    with pytest.raises(FileParserError, match="Unsupported file format"):
        FileParserService().parse_bytes(filename="archive.zip", raw_content=b"not supported")


def test_parse_rejects_empty_or_unreadable_text() -> None:
    with pytest.raises(FileParserError, match="empty"):
        FileParserService().parse_bytes(filename="empty.txt", raw_content=b"")

    with pytest.raises(FileParserError, match="no readable text"):
        FileParserService().parse_bytes(filename="blank.md", raw_content=b"   \n")


@pytest.mark.parametrize(
    ("filename", "expected_message"),
    [
        ("broken.pdf", "Failed to parse PDF"),
        ("broken.docx", "Failed to parse DOCX"),
        ("broken.xlsx", "Failed to parse XLSX"),
    ],
)
def test_parse_reports_clear_errors_for_corrupt_business_files(
    filename: str,
    expected_message: str,
) -> None:
    with pytest.raises(FileParserError, match=expected_message):
        FileParserService().parse_bytes(filename=filename, raw_content=b"not a valid document")
