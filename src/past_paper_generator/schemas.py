"""Data models and validation utilities for the past paper generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

ALLOWED_SUBJECTS = {
    "maths": "Mathematics",
    "english": "English Language",
    "combined science": "Combined Science",
    "biology": "Biology",
    "chemistry": "Chemistry",
    "physics": "Physics",
}

ALLOWED_EXAM_BOARDS = {
    "aqa": "AQA",
    "ocr": "OCR",
    "edexcel": "Edexcel",
}

ALLOWED_TIERS = {
    "foundation": "Foundation",
    "higher": "Higher",
}

ALLOWED_DIFFICULTIES = {
    "easy": "Easy",
    "standard": "Standard",
    "challenging": "Challenging",
}


class ValidationError(ValueError):
    """Raised when incoming parameters fail validation."""


@dataclass(slots=True)
class GenerationParams:
    """Structured parameters captured from the UI or CLI."""

    subject: str
    exam_board: str
    tier: str
    difficulty: str
    num_questions: int

    def normalised(self) -> "GenerationParams":
        """Return a new instance with canonical casing for enums."""

        return GenerationParams(
            subject=_normalise_choice(self.subject, ALLOWED_SUBJECTS.keys()),
            exam_board=_normalise_choice(self.exam_board, ALLOWED_EXAM_BOARDS.keys()),
            tier=_normalise_choice(self.tier, ALLOWED_TIERS.keys()),
            difficulty=_normalise_choice(self.difficulty, ALLOWED_DIFFICULTIES.keys()),
            num_questions=self.num_questions,
        )

    def validate(self) -> "GenerationParams":
        """Validate parameters and return the normalised version."""

        normalised = self.normalised()

        if normalised.subject not in ALLOWED_SUBJECTS:
            raise ValidationError(
                f"Unsupported subject '{self.subject}'. Supported values: {', '.join(sorted(ALLOWED_SUBJECTS))}."
            )
        if normalised.exam_board not in ALLOWED_EXAM_BOARDS:
            raise ValidationError(
                f"Unsupported exam board '{self.exam_board}'. Supported values: {', '.join(sorted(ALLOWED_EXAM_BOARDS))}."
            )
        if normalised.tier not in ALLOWED_TIERS:
            raise ValidationError(
                f"Unsupported tier '{self.tier}'. Supported values: {', '.join(sorted(ALLOWED_TIERS))}."
            )
        if normalised.difficulty not in ALLOWED_DIFFICULTIES:
            raise ValidationError(
                f"Unsupported difficulty '{self.difficulty}'. Supported values: {', '.join(sorted(ALLOWED_DIFFICULTIES))}."
            )
        if not 1 <= normalised.num_questions <= 30:
            raise ValidationError("Number of questions must be between 1 and 30.")

        return normalised


@dataclass(slots=True)
class Question:
    """Represents an exam question."""

    number: int
    prompt: str
    marks: int
    topic: str
    difficulty: str


@dataclass(slots=True)
class MarkSchemeEntry:
    """Represents a mark scheme entry for a single question."""

    number: int
    answer: str
    marks: int
    notes: str | None = None


@dataclass(slots=True)
class PaperBundle:
    """Bundle returned after generating a paper and mark scheme."""

    params: GenerationParams
    questions: Sequence[Question]
    mark_scheme: Sequence[MarkSchemeEntry]
    paper_pdf: Path
    mark_scheme_pdf: Path
    created_at: datetime = field(default_factory=datetime.utcnow)


def _normalise_choice(value: str, options: Iterable[str]) -> str:
    lower_value = value.strip().lower()
    for option in options:
        if lower_value == option:
            return option
    return lower_value
