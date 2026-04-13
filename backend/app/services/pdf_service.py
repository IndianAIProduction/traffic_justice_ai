"""
PDF Service: Generates formal complaint PDF documents.
Uses fpdf2 with system Unicode fonts for Indian language support.
"""
import os
import glob
from typing import Optional, List
from datetime import datetime, timezone

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    FPDF = None
    HAS_FPDF = False
    logger.warning("fpdf2 not installed. PDF generation disabled. Run: pip install fpdf2")


SYSTEM_FONT_PATHS = [
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _find_unicode_font() -> tuple[Optional[str], Optional[str]]:
    """Find a Unicode-capable TTF font on the system. Returns (regular, bold) paths."""
    font_pairs = [
        (
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        (
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ),
    ]
    for regular, bold in font_pairs:
        if os.path.isfile(regular):
            bold_path = bold if os.path.isfile(bold) else regular
            return regular, bold_path

    # Last resort: search for any .ttf file
    for ttf in glob.glob("/usr/share/fonts/**/*.ttf", recursive=True):
        return ttf, ttf

    return None, None


def generate_complaint_pdf(
    complaint_id: str,
    complainant_name: str,
    complainant_email: str,
    complaint_type: str,
    state_name: str,
    portal_name: str,
    complaint_text: str,
    recipient: Optional[str] = None,
    subject: Optional[str] = None,
    legal_citations: Optional[List[str]] = None,
    relief_sought: Optional[str] = None,
    emails_sent_to: Optional[List[str]] = None,
    portal_url: Optional[str] = None,
) -> Optional[str]:
    """Generate a formal complaint PDF and return the file path."""

    if not HAS_FPDF:
        logger.warning("fpdf2 not installed, skipping PDF generation")
        return None

    output_dir = os.path.join(settings.evidence_storage_path, "complaint_pdfs")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"complaint_{complaint_id[:8]}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)

    regular_font, bold_font = _find_unicode_font()

    try:
        pdf = FPDF()
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=25)

        use_unicode = regular_font is not None
        font_family = "CustomFont"

        if use_unicode:
            pdf.add_font(font_family, "", regular_font, uni=True)
            if bold_font and bold_font != regular_font:
                pdf.add_font(font_family, "B", bold_font, uni=True)
            else:
                pdf.add_font(font_family, "B", regular_font, uni=True)
        else:
            font_family = "Helvetica"
            logger.warning("No Unicode font found; PDF will use Helvetica (Latin only)")

        pdf.add_page()

        # Header
        pdf.set_font(font_family, "B", 14)
        pdf.cell(0, 10, "FORMAL GRIEVANCE COMPLAINT", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, "", 8)
        pdf.cell(0, 5, "Generated via Traffic Justice AI Platform", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(6)

        # Date and reference
        date_str = datetime.now(timezone.utc).strftime("%d %B %Y")
        pdf.set_font(font_family, "", 10)
        pdf.cell(0, 6, f"Date: {date_str}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Reference No: TJ-{complaint_id[:8].upper()}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Complaint Type: {complaint_type.replace('_', ' ').title()}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"State: {state_name}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Recipient
        if recipient:
            pdf.set_font(font_family, "B", 10)
            pdf.cell(0, 6, "To:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(font_family, "", 10)
            pdf.multi_cell(0, 6, recipient)
            pdf.ln(3)

        # Subject
        if subject:
            pdf.set_font(font_family, "B", 11)
            pdf.multi_cell(0, 6, f"Subject: {subject}")
            pdf.ln(3)

        # Complaint body
        pdf.set_font(font_family, "", 10)
        pdf.multi_cell(0, 6, complaint_text)
        pdf.ln(4)

        # Legal citations
        if legal_citations:
            pdf.set_font(font_family, "B", 10)
            pdf.cell(0, 7, "Applicable Legal Provisions:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(font_family, "", 10)
            for citation in legal_citations:
                pdf.cell(0, 6, f"  - {citation}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        # Relief sought
        if relief_sought:
            pdf.set_font(font_family, "B", 10)
            pdf.cell(0, 7, "Relief Sought:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(font_family, "", 10)
            pdf.multi_cell(0, 6, relief_sought)
            pdf.ln(3)

        # Submission details
        pdf.set_font(font_family, "B", 10)
        pdf.cell(0, 7, "Submission Details:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, "", 10)
        pdf.cell(0, 6, f"Portal: {portal_name}", new_x="LMARGIN", new_y="NEXT")
        if portal_url:
            pdf.cell(0, 6, f"Portal URL: {portal_url}", new_x="LMARGIN", new_y="NEXT")
        if emails_sent_to:
            pdf.cell(0, 6, f"Emailed to: {', '.join(emails_sent_to)}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # Signature block
        pdf.set_font(font_family, "", 10)
        pdf.cell(0, 6, "Yours faithfully,", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        pdf.cell(0, 6, complainant_name, new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Email: {complainant_email}", new_x="LMARGIN", new_y="NEXT")

        # Footer
        pdf.set_y(-20)
        pdf.set_font(font_family, "", 7)
        pdf.cell(
            0, 5,
            "This document is computer-generated. Please verify details before official submission.",
            align="C",
        )

        pdf.output(filepath)
        logger.info(f"Complaint PDF generated: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to generate complaint PDF: {e}")
        return None
