"""Generate reflection-driven revision packs for learners."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from .schemas import (
    PaperBundle,
    Question,
    ResourceLink,
    RevisionFlashcard,
    RevisionNote,
    RevisionPlan,
)


@dataclass(slots=True)
class ReflectionSubmission:
    """User-provided reflection about exam performance."""

    weaknesses: str
    reflection: str
    improvements: str

    def keywords(self) -> set[str]:
        """Simple keyword extraction for matching topics."""

        text = f"{self.weaknesses} {self.reflection} {self.improvements}".lower()
        tokens = {word.strip(".,!?;:") for word in text.split() if len(word) > 3}
        return {token for token in tokens if token}


def build_revision_plan(bundle: PaperBundle, submission: ReflectionSubmission) -> RevisionPlan:
    """Create a targeted revision plan based on a learner's reflections."""

    focus_questions = _select_focus_questions(bundle, submission)
    focus_topics = tuple({question.topic for question in focus_questions}) or (
        bundle.questions[0].topic,
    )

    flashcards = []
    notes = []
    resources: list[ResourceLink] = []
    seen_resources: set[str] = set()

    for question in focus_questions:
        flashcards.append(
            RevisionFlashcard(
                topic=question.topic,
                front=f"{question.topic}: {question.skill_focus}",
                back=_flashcard_back(question),
            )
        )

        notes.append(
            RevisionNote(
                heading=f"Mastering {question.skill_focus}",
                bullet_points=(
                    f"Allocate ~{question.recommended_time_minutes} minutes and outline the method first.",
                    f"Key strategy: {question.strategy}",
                    f"Examiner expects: {question.guidance}",
                ),
            )
        )

        for link in question.resources:
            if link not in seen_resources:
                seen_resources.add(link)
                resources.append(_resource_from_link(question.topic, link))

    next_steps = _next_steps(submission)

    return RevisionPlan(
        focus_topics=focus_topics,
        flashcards=tuple(flashcards),
        notes=tuple(notes),
        resources=tuple(resources),
        next_steps=tuple(next_steps),
    )


def _select_focus_questions(
    bundle: PaperBundle, submission: ReflectionSubmission
) -> List[Question]:
    keywords = submission.keywords()
    scored: List[Tuple[int, int]] = []

    for idx, question in enumerate(bundle.questions):
        score = 0
        topic_tokens = {token.lower() for token in question.topic.split()}
        if keywords & topic_tokens:
            score += 3
        if any(keyword in question.prompt.lower() for keyword in keywords):
            score += 2
        if question.difficulty.lower() == "challenging":
            score += 1
        if question.marks >= 4:
            score += 1
        scored.append((score, idx))

    if not scored:
        return bundle.questions

    ranked = [bundle.questions[idx] for score, idx in sorted(scored, reverse=True) if score > 0]
    return ranked[:3] or bundle.questions[: min(3, len(bundle.questions))]


def _flashcard_back(question) -> str:
    return (
        f"Method: {question.strategy}. Guidance: {question.guidance}.\n"
        f"Spec reference: {question.syllabus_reference}."
    )


def _resource_from_link(topic: str, link: str) -> ResourceLink:
    if "bbc" in link:
        title = f"BBC Bitesize: {topic}"
    elif "khanacademy" in link:
        title = f"Khan Academy primer on {topic.lower()}"
    elif "aqa" in link:
        title = f"AQA guidance for {topic.lower()}"
    else:
        title = f"Further reading: {topic}"

    description = "Curated resource aligned with the specification focus."
    return ResourceLink(title=title, url=link, description=description)


def _next_steps(submission: ReflectionSubmission) -> Iterable[str]:
    steps = [
        "Schedule a timed practice using the regenerated flashcards.",
        "Teach the concept aloud to check understanding (Feynman technique).",
    ]
    if submission.improvements:
        steps.append(f"Action from learner: {submission.improvements.strip()}.")
    steps.append("Revisit this generator in 48 hours to consolidate gains.")
    return steps
