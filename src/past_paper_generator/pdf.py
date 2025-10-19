"""PDF rendering utilities for the exam paper and mark scheme."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .schemas import GenerationParams, MarkSchemeEntry, Question


def build_exam_pdf(path: Path, params: GenerationParams, questions: Sequence[Question]) -> Path:
    """Render the exam paper PDF and return the resulting path."""

    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=54, bottomMargin=36)
    styles = _styles()
    story = [
        Paragraph("GCSE Past Paper", styles["title"]),
        Spacer(1, 12),
        Paragraph(_metadata_line(params), styles["metadata"]),
        Spacer(1, 24),
    ]

    for question in questions:
        story.extend(
            [
                Paragraph(f"Question {question.number} - {question.topic}", styles["question_heading"]),
                Paragraph(f"Marks: {question.marks} | Difficulty: {question.difficulty}", styles["metadata"]),
                Spacer(1, 6),
                Paragraph(question.prompt, styles["body"]),
                Spacer(1, 18),
            ]
        )

    doc.build(story)
    return path


def build_mark_scheme_pdf(path: Path, params: GenerationParams, entries: Sequence[MarkSchemeEntry]) -> Path:
    """Render the mark scheme PDF and return the resulting path."""

    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=54, bottomMargin=36)
    styles = _styles()
    story = [
        _branding_banner(styles),
        Spacer(1, 10),
        Paragraph("GCSE Mark Scheme", styles["title"]),
        Spacer(1, 6),
        Paragraph(_metadata_line(params), styles["metadata"]),
        Spacer(1, 18),
    ]

    for entry in entries:
        story.extend(_mark_scheme_section(entry, styles))
        story.append(Spacer(1, 16))

    doc.build(story)
    return path


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "TitleStyle",
            parent=base["Heading1"],
            alignment=1,
            fontSize=20,
            textColor=colors.HexColor("#1b4965"),
            spaceAfter=12,
        ),
        "metadata": ParagraphStyle(
            "MetadataStyle",
            parent=base["BodyText"],
            textColor=colors.HexColor("#555555"),
            fontSize=10,
        ),
        "banner_title": ParagraphStyle(
            "BannerTitle",
            parent=base["Heading2"],
            fontSize=16,
            textColor=colors.white,
            leading=18,
        ),
        "banner_subtitle": ParagraphStyle(
            "BannerSubtitle",
            parent=base["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#f0f4f8"),
        ),
        "body": ParagraphStyle(
            "BodyStyle",
            parent=base["BodyText"],
            fontSize=12,
            leading=16,
        ),
        "question_heading": ParagraphStyle(
            "QuestionHeading",
            parent=base["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#102a43"),
            spaceAfter=6,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading3"],
            fontSize=12,
            textColor=colors.HexColor("#1b4965"),
            spaceAfter=4,
        ),
        "marks_badge": ParagraphStyle(
            "MarksBadge",
            parent=base["BodyText"],
            fontSize=11,
            alignment=1,
            textColor=colors.white,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#0a2540"),
            leading=12,
        ),
        "notes_body": ParagraphStyle(
            "NotesBody",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
        ),
    }
    return styles


def _metadata_line(params: GenerationParams) -> str:
    return (
        f"Subject: {params.subject.title()} | Exam board: {params.exam_board.upper()} | "
        f"Tier: {params.tier.title()} | Difficulty: {params.difficulty.title()}"
    )


def _branding_banner(styles: dict[str, ParagraphStyle]) -> Table:
    banner = Table(
        [
            [
                Paragraph("<b>AFE Assessment</b>", styles["banner_title"]),
                Paragraph("Dedicated to ambitious GCSE learners", styles["banner_subtitle"]),
            ]
        ],
        colWidths=[320, 180],
        hAlign="LEFT",
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#102a43")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#0b1d32")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return banner


def _mark_scheme_section(entry: MarkSchemeEntry, styles: dict[str, ParagraphStyle]) -> list:
    marks_text = f"{entry.marks} mark" if entry.marks == 1 else f"{entry.marks} marks"
    header = Table(
        [
            [
                Paragraph(f"Question {entry.number}", styles["section_heading"]),
                Paragraph(marks_text, styles["marks_badge"]),
            ]
        ],
        colWidths=[360, 120],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#d9e2ec")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#1b4965")),
                ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#9fb3c8")),
                ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#0f1f2f")),
                ("LEFTPADDING", (0, 0), (0, 0), 10),
                ("RIGHTPADDING", (1, 0), (1, 0), 6),
                ("LEFTPADDING", (1, 0), (1, 0), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    panel_rows = [
        [
            Paragraph("<b>Marking guidance</b>", styles["table_header"]),
            Paragraph("<b>Additional guidance</b>", styles["table_header"]),
        ],
        [
            Paragraph(entry.answer, styles["body"]),
            Paragraph(entry.notes or "Use teacher discretion for alternative valid methods.", styles["notes_body"]),
        ],
    ]

    panel = Table(panel_rows, colWidths=[360, 120])
    panel.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#9fb3c8")),
                ("LINEBEFORE", (1, 1), (1, 1), 0.5, colors.HexColor("#d9e2ec")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return [header, panel]
