"""Core orchestration logic for generating papers and mark schemes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from .llm_stub import GeneratedQuestion, MockMarkSchemeLLM, MockQuestionLLM
from .pdf import build_exam_pdf, build_mark_scheme_pdf
from .schemas import GenerationParams, MarkSchemeEntry, PaperBundle, Question


class PastPaperService:
    """High-level API to generate GCSE past papers."""

    def __init__(
        self,
        question_llm: MockQuestionLLM | None = None,
        markscheme_llm: MockMarkSchemeLLM | None = None,
    ) -> None:
        self._question_llm = question_llm or MockQuestionLLM()
        self._markscheme_llm = markscheme_llm or MockMarkSchemeLLM()

    def generate(self, params: GenerationParams, output_dir: Path | str = "outputs") -> PaperBundle:
        validated = params.validate()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_questions = self._question_llm.generate(validated)
        questions = _to_questions(generated_questions)
        mark_scheme_entries = _build_mark_scheme(self._markscheme_llm.generate(generated_questions))

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        slug = f"{validated.subject.replace(' ', '_')}_{validated.exam_board}_{timestamp}"
        paper_pdf = output_dir / f"{slug}_paper.pdf"
        mark_scheme_pdf = output_dir / f"{slug}_mark_scheme.pdf"

        build_exam_pdf(paper_pdf, validated, questions)
        build_mark_scheme_pdf(mark_scheme_pdf, validated, mark_scheme_entries)

        return PaperBundle(
            params=validated,
            questions=questions,
            mark_scheme=mark_scheme_entries,
            paper_pdf=paper_pdf,
            mark_scheme_pdf=mark_scheme_pdf,
        )


def _to_questions(generated: Sequence[GeneratedQuestion]) -> Sequence[Question]:
    return [
        Question(
            number=item.number,
            prompt=item.prompt,
            topic=item.topic,
            difficulty=item.difficulty,
            marks=item.marks,
        )
        for item in generated
    ]


def _build_mark_scheme(generated: Iterable[GeneratedQuestion]) -> Sequence[MarkSchemeEntry]:
    return [
        MarkSchemeEntry(
            number=item.number,
            answer=item.answer,
            marks=item.marks,
            notes=item.notes,
        )
        for item in generated
    ]
