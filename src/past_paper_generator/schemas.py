"""Data models and validation utilities for the past paper generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    """Represents an exam question with learning logistics."""

    number: int
    prompt: str
    marks: int
    topic: str
    difficulty: str
    recommended_time_minutes: int
    skill_focus: str
    strategy: str
    guidance: str
    syllabus_reference: str
    resources: tuple[str, ...] = ()


@dataclass(slots=True)
class MarkSchemeEntry:
    """Represents a mark scheme entry for a single question."""

    number: int
    answer: str
    marks: int
    method_breakdown: str
    common_pitfalls: str
    examiner_notes: str
    notes: str | None = None


@dataclass(slots=True)
class Flashcard:
    """Spaced-repetition flashcard enriched with hints and scheduling."""

    id: str
    topic: str
    difficulty: str
    skill_type: str
    front: str
    back: str
    hints: tuple[str, ...] = ()
    why_wrong: str | None = None
    ease: float = 2.3
    interval_days: int = 1
    due_iso: str = field(
        default_factory=lambda: (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    streak: int = 0


@dataclass(slots=True)
class QuickCheck:
    """Low-stakes question with a revealable answer."""

    prompt: str
    answer: str


@dataclass(slots=True)
class NotesSection:
    """Focused summary notes for a single concept."""

    topic: str
    skill_focus: str
    key_idea: str
    formulas: tuple[str, ...]
    monospaced_formulas: bool
    mini_example_setup: str
    mini_example_steps: tuple[str, ...]
    common_traps: tuple[str, ...]
    quick_checks: tuple[QuickCheck, ...]
    anchor_problem: str | None = None
    anchor_solution: str | None = None


@dataclass(slots=True)
class ResourceItem:
    """High-impact follow-up material."""

    topic: str
    type: str
    title: str
    link_or_query: str
    est_time_min: int
    why_this: str


@dataclass(slots=True)
class StudyMaterials:
    """Collection of study artefacts derived from a generated paper."""

    flashcards: tuple[Flashcard, ...]
    notes: tuple[NotesSection, ...]
    resources: tuple[ResourceItem, ...]


@dataclass(slots=True)
class PaperBundle:
    """Bundle returned after generating a paper and mark scheme."""

    params: GenerationParams
    questions: Sequence[Question]
    mark_scheme: Sequence[MarkSchemeEntry]
    paper_pdf: Path
    mark_scheme_pdf: Path
    slug: str
    total_marks: int
    estimated_duration_minutes: int
    created_at: datetime = field(default_factory=datetime.utcnow)


def _normalise_choice(value: str, options: Iterable[str]) -> str:
    lower_value = value.strip().lower()
    for option in options:
        if lower_value == option:
            return option
    return lower_value
