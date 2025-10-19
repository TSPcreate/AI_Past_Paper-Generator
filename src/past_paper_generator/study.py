"""Build study materials derived from generated papers."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence

from .schemas import (
    Flashcard,
    MarkSchemeEntry,
    NotesSection,
    PaperBundle,
    QuickCheck,
    Question,
    ResourceItem,
    StudyMaterials,
)


def build_study_materials(bundle: PaperBundle) -> StudyMaterials:
    """Create flashcards, summary notes and resource suggestions."""

    flashcards = tuple(_build_flashcards(bundle.slug, bundle.questions, bundle.mark_scheme))
    notes = tuple(_build_notes(bundle.questions, bundle.mark_scheme, bundle.params.subject))
    resources = tuple(_build_resources(bundle.questions, bundle.params.subject))
    return StudyMaterials(flashcards=flashcards, notes=notes, resources=resources)


def _build_flashcards(
    slug: str, questions: Sequence[Question], mark_scheme: Sequence[MarkSchemeEntry]
) -> Iterable[Flashcard]:
    now = datetime.utcnow()
    for question, entry in zip(questions, mark_scheme):
        hints = _flashcard_hints(question, entry)
        yield Flashcard(
            id=f"{slug}-q{question.number}",
            topic=question.topic,
            difficulty=question.difficulty,
            skill_type=question.skill_focus,
            front=f"Q{question.number}: {question.prompt}",
            back=entry.answer,
            hints=hints,
            why_wrong=entry.common_pitfalls,
            ease=2.3,
            interval_days=1,
            due_iso=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            streak=0,
        )


def _flashcard_hints(question: Question, entry: MarkSchemeEntry) -> tuple[str, ...]:
    hints: list[str] = []
    if question.strategy:
        hints.append(question.strategy)
    if question.guidance and question.guidance not in hints:
        hints.append(question.guidance)
    method_bits = [bit.strip() for bit in entry.method_breakdown.replace("→", "->").split(".")]
    for bit in method_bits:
        if bit and bit not in hints and len(hints) < 3:
            hints.append(bit)
    if question.syllabus_reference and question.syllabus_reference not in hints:
        hints.append(f"Spec: {question.syllabus_reference}")
    return tuple(hints[:3])


def _build_notes(
    questions: Sequence[Question],
    mark_scheme: Sequence[MarkSchemeEntry],
    subject: str,
) -> Iterable[NotesSection]:
    for question, entry in zip(questions, mark_scheme):
        key_idea = f"{question.skill_focus} in {question.topic}".strip()
        formulas = _note_formulas(question, entry)
        steps = _steps(entry)
        quick_checks = (
            QuickCheck(
                prompt=f"What is the first move when tackling {question.topic.lower()}?",
                answer=steps[0] if steps else entry.method_breakdown,
            ),
            QuickCheck(
                prompt=f"How many marks could you earn for this question?",
                answer=str(entry.marks),
            ),
            QuickCheck(
                prompt=f"Name a common pitfall to avoid for {question.topic.lower()}.",
                answer=entry.common_pitfalls,
            ),
        )
        anchor_problem = question.prompt if question.marks >= 3 else None
        anchor_solution = entry.answer if anchor_problem else None

        yield NotesSection(
            topic=question.topic,
            skill_focus=question.skill_focus,
            key_idea=key_idea,
            formulas=formulas,
            monospaced_formulas=_should_use_mono(subject, formulas),
            mini_example_setup=f"Variation on question {question.number}:",
            mini_example_steps=steps or (entry.method_breakdown,),
            common_traps=_traps(entry.common_pitfalls),
            quick_checks=quick_checks,
            anchor_problem=anchor_problem,
            anchor_solution=anchor_solution,
        )


def _note_formulas(question: Question, entry: MarkSchemeEntry) -> tuple[str, ...]:
    items = [
        question.strategy,
        question.guidance,
        f"Spec reference: {question.syllabus_reference}",
    ]
    if entry.notes:
        items.append(entry.notes)
    # Remove empties while preserving order.
    seen: set[str] = set()
    formulas: list[str] = []
    for item in items:
        if not item:
            continue
        trimmed = item.strip()
        if trimmed and trimmed not in seen:
            seen.add(trimmed)
            formulas.append(trimmed)
    return tuple(formulas[:4])


def _steps(entry: MarkSchemeEntry) -> tuple[str, ...]:
    raw_steps = [part.strip() for part in entry.method_breakdown.replace("→", "->").split(".")]
    steps = tuple(step for step in raw_steps if step)
    return steps or (entry.method_breakdown.strip(),)


def _traps(text: str) -> tuple[str, ...]:
    parts = [part.strip(" .") for part in text.replace(";", ".").split(".")]
    traps = tuple(part for part in parts if part)
    return traps or (text.strip(),)


def _should_use_mono(subject: str, formulas: Sequence[str]) -> bool:
    if subject.lower() in {"maths", "chemistry", "physics"}:
        return True
    return any(char in formula for formula in formulas for char in "=±×÷→")


def _build_resources(questions: Sequence[Question], subject: str) -> Iterable[ResourceItem]:
    seen: set[tuple[str, str]] = set()
    for question in questions:
        topic = question.topic
        for url in question.resources:
            key = (topic, url)
            if key in seen:
                continue
            seen.add(key)
            resource_type = _resource_type(url)
            why = f"Reinforces {question.skill_focus.lower()} with exam-style practice."
            yield ResourceItem(
                topic=topic,
                type=resource_type,
                title=_resource_title(topic, url),
                link_or_query=url,
                est_time_min=12 if resource_type == "Article" else 18,
                why_this=why,
            )
        query = f"query:{subject.title()} {topic} GCSE revision"
        key = (topic, query)
        if key not in seen:
            seen.add(key)
            yield ResourceItem(
                topic=topic,
                type="Search",
                title=f"Wider reading on {topic}",
                link_or_query=query,
                est_time_min=10,
                why_this="Compare at least two trusted sources for consolidation.",
            )


def _resource_type(url: str) -> str:
    lowered = url.lower()
    if lowered.startswith("query:"):
        return "Search"
    if "youtube" in lowered or "video" in lowered:
        return "Video"
    if "podcast" in lowered:
        return "Audio"
    return "Article"


def _resource_title(topic: str, url: str) -> str:
    if url.lower().startswith("query:"):
        return f"Search for {topic}"
    if "bbc" in url.lower():
        return f"BBC Bitesize: {topic}"
    if "aqa" in url.lower():
        return f"AQA guidance on {topic.lower()}"
    if "khan" in url.lower():
        return f"Khan Academy: {topic}"
    return f"Further study: {topic}"
