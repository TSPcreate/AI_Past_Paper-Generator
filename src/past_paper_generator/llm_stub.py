"""A lightweight, deterministic LLM stand-in used for local development."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List

from .schemas import GenerationParams


@dataclass(slots=True)
class GeneratedQuestion:
    number: int
    prompt: str
    topic: str
    difficulty: str
    marks: int
    answer: str
    notes: str | None = None


class MockQuestionLLM:
    """Generate exam-style questions using canned templates."""

    _QUESTION_BANK: Dict[str, List[Dict[str, str]]] = {
        "maths": [
            {
                "prompt": "Solve {a}x + {b} = {c}.",
                "answer": "x = {solution}",
                "topic": "Linear equations",
            },
            {
                "prompt": "A right-angled triangle has legs {a} cm and {b} cm. Calculate the hypotenuse.",
                "answer": "{hypotenuse} cm",
                "topic": "Pythagoras' theorem",
            },
            {
                "prompt": "Simplify the expression: {a}x^2 - {b}x + {c}x^2.",
                "answer": "{simplified}x^2 - {b}x",
                "topic": "Collecting like terms",
            },
        ],
        "english": [
            {
                "prompt": "Read the extract about perseverance and explain how the writer uses language to inspire the reader.",
                "answer": "Identify emotive verbs, positive imagery, and direct address.",
                "topic": "Language analysis",
            },
            {
                "prompt": "Write a persuasive speech encouraging students to take part in community volunteering.",
                "answer": "Speech should include rhetorical questions, statistics, and a clear call to action.",
                "topic": "Transactional writing",
            },
            {
                "prompt": "Compare how the theme of ambition is presented in two texts you have studied.",
                "answer": "Discuss character motivations, narrative outcomes, and authorial methods.",
                "topic": "Comparative essay",
            },
        ],
        "combined science": [
            {
                "prompt": "Describe the process of photosynthesis and state two factors that affect its rate.",
                "answer": "Light intensity and temperature affect the rate; carbon dioxide is also essential.",
                "topic": "Biology - photosynthesis",
            },
            {
                "prompt": "Explain the difference between series and parallel circuits, including the effect on current.",
                "answer": "Series: current constant; Parallel: currents split across branches.",
                "topic": "Physics - electricity",
            },
            {
                "prompt": "State the law of conservation of mass and apply it to a chemical reaction example.",
                "answer": "Mass is conserved; total mass of reactants equals products.",
                "topic": "Chemistry - reactions",
            },
        ],
        "biology": [
            {
                "prompt": "Describe how enzymes catalyse reactions and what happens when they denature.",
                "answer": "Enzymes lower activation energy; denaturing changes the active site shape.",
                "topic": "Biological molecules",
            },
            {
                "prompt": "Explain the stages of mitosis and why it is important for growth.",
                "answer": "Prophase, metaphase, anaphase, telophase; produces identical daughter cells.",
                "topic": "Cell division",
            },
        ],
        "chemistry": [
            {
                "prompt": "Balance the chemical equation: {equation}.",
                "answer": "{balanced}",
                "topic": "Chemical equations",
            },
            {
                "prompt": "Describe how ionic bonds are formed between metals and non-metals.",
                "answer": "Electrons transfer from metal to non-metal forming oppositely charged ions.",
                "topic": "Bonding",
            },
        ],
        "physics": [
            {
                "prompt": "A car accelerates from {v1} m/s to {v2} m/s in {t} s. Calculate the acceleration.",
                "answer": "Acceleration = {acceleration} m/s^2",
                "topic": "Kinematics",
            },
            {
                "prompt": "State Newton's three laws of motion and provide an everyday example for each.",
                "answer": "Inertia, F=ma, action-reaction; examples include seatbelts, pushing trolleys, rocket propulsion.",
                "topic": "Forces",
            },
        ],
    }

    _TIER_HINTS = {
        "foundation": "Focus on core concepts with scaffolded guidance.",
        "higher": "Expect multi-step reasoning and precise terminology.",
    }

    _DIFFICULTY_MARKS = {
        "easy": (1, 2),
        "standard": (2, 4),
        "challenging": (4, 6),
    }

    def generate(self, params: GenerationParams) -> List[GeneratedQuestion]:
        subject_bank = self._QUESTION_BANK.get(params.subject, self._QUESTION_BANK["maths"])
        rand = random.Random(self._seed(params))
        questions: List[GeneratedQuestion] = []

        for number in range(1, params.num_questions + 1):
            template = subject_bank[(number - 1) % len(subject_bank)]
            marks = rand.randint(*self._DIFFICULTY_MARKS.get(params.difficulty, (2, 4)))
            prompt = self._fill_template(template["prompt"], rand)
            answer = self._fill_template(template["answer"], rand)
            notes = self._TIER_HINTS.get(params.tier)
            questions.append(
                GeneratedQuestion(
                    number=number,
                    prompt=prompt,
                    topic=template["topic"],
                    difficulty=params.difficulty.title(),
                    marks=marks,
                    answer=answer,
                    notes=notes,
                )
            )

        return questions

    def _seed(self, params: GenerationParams) -> int:
        return hash((params.subject, params.exam_board, params.tier, params.difficulty, params.num_questions)) & 0xFFFFFFFF

    def _fill_template(self, template: str, rand: random.Random) -> str:
        substitutions = {
            "a": rand.randint(2, 12),
            "b": rand.randint(2, 12),
            "c": rand.randint(4, 20),
            "solution": rand.randint(1, 9),
            "hypotenuse": round((rand.randint(3, 9) ** 2 + rand.randint(3, 9) ** 2) ** 0.5, 2),
            "simplified": rand.randint(2, 9),
            "equation": "H2 + O2 -> H2O",
            "balanced": "2H2 + O2 -> 2H2O",
            "v1": rand.randint(0, 5),
            "v2": rand.randint(10, 25),
            "t": rand.randint(2, 10),
            "acceleration": round(rand.uniform(1.0, 4.5), 2),
        }
        try:
            return template.format(**substitutions)
        except KeyError:
            return template


class MockMarkSchemeLLM:
    """Generate mark scheme entries derived from question data."""

    def generate(self, questions: Iterable[GeneratedQuestion]) -> List[GeneratedQuestion]:
        return [question for question in questions]
