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
        Paragraph("GCSE Mark Scheme", styles["title"]),
        Spacer(1, 12),
        Paragraph(_metadata_line(params), styles["metadata"]),
        Spacer(1, 18),
    ]

    table_data = [["Question", "Expected answer", "Marks", "Notes"]]
    for entry in entries:
        table_data.append(
            [
                f"{entry.number}",
                entry.answer,
                str(entry.marks),
                entry.notes or "",
            ]
        )

    table = Table(table_data, colWidths=[54, 270, 54, 108])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b4965")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f7f7f7")]),
            ]
        )
    )

    story.append(table)
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
    }
    return styles


def _metadata_line(params: GenerationParams) -> str:
    return (
        f"Subject: {params.subject.title()} | Exam board: {params.exam_board.upper()} | "
        f"Tier: {params.tier.title()} | Difficulty: {params.difficulty.title()}"
    )
