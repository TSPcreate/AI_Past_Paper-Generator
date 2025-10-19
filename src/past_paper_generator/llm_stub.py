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
    skill_focus: str = "Core reasoning"
    strategy: str = "Show all steps"
    guidance: str = "Work methodically."
    syllabus_reference: str = "General"
    estimated_minutes: int = 3
    resources: tuple[str, ...] = ()
    method_breakdown: str = "Identify the key steps and justify each one."
    common_pitfalls: str = "Watch out for algebraic slips."
    examiner_notes: str = "Award follow-through marks for clear reasoning."


class MockQuestionLLM:
    """Generate exam-style questions using canned templates."""

    _QUESTION_BANK: Dict[str, List[Dict[str, str]]] = {
        "maths": [
            {
                "prompt": "Solve {a}x + {b} = {c}.",
                "answer": "x = {solution}",
                "topic": "Linear equations",
                "skill_focus": "Solving linear equations",
                "strategy": "Isolate x by balancing both sides.",
                "guidance": "Subtract the constant then divide by the coefficient of x.",
                "syllabus": "AQA GCSE Maths 1.3",
                "resources": (
                    "https://www.bbc.co.uk/bitesize/guides/zqhyb82/revision/3",
                    "https://mathsgenie.co.uk/algebra.html",
                ),
            },
            {
                "prompt": "A right-angled triangle has legs {a} cm and {b} cm. Calculate the hypotenuse.",
                "answer": "{hypotenuse} cm",
                "topic": "Pythagoras' theorem",
                "skill_focus": "Applying Pythagoras",
                "strategy": "Square the shorter sides, sum them and take the square root.",
                "guidance": "Check the triangle is right-angled before applying the formula.",
                "syllabus": "AQA GCSE Maths 4.2",
                "resources": (
                    "https://corbettmaths.com/2012/08/23/pythagoras-theorem/",
                ),
            },
            {
                "prompt": "Simplify the expression: {a}x^2 - {b}x + {c}x^2.",
                "answer": "{simplified}x^2 - {b}x",
                "topic": "Collecting like terms",
                "skill_focus": "Collecting like terms",
                "strategy": "Group the x^2 terms then simplify.",
                "guidance": "Underline like terms to avoid missing coefficients.",
                "syllabus": "AQA GCSE Maths 1.1",
                "resources": (
                    "https://sparx.co.uk/using-like-terms",
                ),
            },
        ],
        "english": [
            {
                "prompt": "Read the extract about perseverance and explain how the writer uses language to inspire the reader.",
                "answer": "Identify emotive verbs, positive imagery, and direct address.",
                "topic": "Language analysis",
                "skill_focus": "Analysing persuasive language",
                "strategy": "Annotate techniques then link to reader impact.",
                "guidance": "Use short quotations and explore specific word choices.",
                "syllabus": "AQA GCSE English Language Paper 1",
                "resources": (
                    "https://www.aqa.org.uk/resources/english/gcse/english-language/teach/language-analysis",
                ),
            },
            {
                "prompt": "Write a persuasive speech encouraging students to take part in community volunteering.",
                "answer": "Speech should include rhetorical questions, statistics, and a clear call to action.",
                "topic": "Transactional writing",
                "skill_focus": "Structuring persuasive speeches",
                "strategy": "Use a three-part structure: hook, argument, call to action.",
                "guidance": "Blend facts with emotive appeal to engage listeners.",
                "syllabus": "AQA GCSE English Language Paper 2",
                "resources": (
                    "https://www.bbc.co.uk/bitesize/guides/z9ybcqt/revision/1",
                ),
            },
            {
                "prompt": "Compare how the theme of ambition is presented in two texts you have studied.",
                "answer": "Discuss character motivations, narrative outcomes, and authorial methods.",
                "topic": "Comparative essay",
                "skill_focus": "Comparing texts",
                "strategy": "Alternate between texts while linking back to the question.",
                "guidance": "Choose two clear points of comparison and support with evidence.",
                "syllabus": "AQA GCSE English Literature AO3",
                "resources": (
                    "https://senecalearning.com/en-GB/blog/how-to-compare-poems/",
                ),
            },
        ],
        "combined science": [
            {
                "prompt": "Describe the process of photosynthesis and state two factors that affect its rate.",
                "answer": "Light intensity and temperature affect the rate; carbon dioxide is also essential.",
                "topic": "Biology - photosynthesis",
                "skill_focus": "Explaining biological processes",
                "strategy": "State the word equation then discuss limiting factors.",
                "guidance": "Link each factor to enzyme activity or particle collisions.",
                "syllabus": "AQA GCSE Biology 4.2",
                "resources": (
                    "https://www.aqa.org.uk/resources/science/gcse/biology/teach/photosynthesis",
                ),
            },
            {
                "prompt": "Explain the difference between series and parallel circuits, including the effect on current.",
                "answer": "Series: current constant; Parallel: currents split across branches.",
                "topic": "Physics - electricity",
                "skill_focus": "Comparing circuit behaviour",
                "strategy": "Define each circuit, then contrast potential difference and current.",
                "guidance": "Mention how total resistance changes when bulbs are added.",
                "syllabus": "AQA GCSE Physics 4.2",
                "resources": (
                    "https://www.bbc.co.uk/bitesize/guides/zq7thyc/revision/1",
                ),
            },
            {
                "prompt": "State the law of conservation of mass and apply it to a chemical reaction example.",
                "answer": "Mass is conserved; total mass of reactants equals products.",
                "topic": "Chemistry - reactions",
                "skill_focus": "Interpreting chemical reactions",
                "strategy": "Link particle models to measurable mass.",
                "guidance": "Discuss closed systems and explain mass changes with gases.",
                "syllabus": "AQA GCSE Chemistry 4.3",
                "resources": (
                    "https://www.chemguide.co.uk/physical/basicstates/conservation.html",
                ),
            },
        ],
        "biology": [
            {
                "prompt": "Describe how enzymes catalyse reactions and what happens when they denature.",
                "answer": "Enzymes lower activation energy; denaturing changes the active site shape.",
                "topic": "Biological molecules",
                "skill_focus": "Explaining enzyme action",
                "strategy": "Link substrate binding to shape and temperature effects.",
                "guidance": "Refer to lock-and-key and optimum conditions.",
                "syllabus": "AQA GCSE Biology 4.1.3",
                "resources": (
                    "https://www.bbc.co.uk/bitesize/guides/zv8mqty/revision/1",
                ),
            },
            {
                "prompt": "Explain the stages of mitosis and why it is important for growth.",
                "answer": "Prophase, metaphase, anaphase, telophase; produces identical daughter cells.",
                "topic": "Cell division",
                "skill_focus": "Sequencing cell division",
                "strategy": "Name each phase with a key feature.",
                "guidance": "Clarify difference between mitosis and cytokinesis.",
                "syllabus": "AQA GCSE Biology 4.1.2",
                "resources": (
                    "https://www.khanacademy.org/science/high-school-biology/hs-cells/hs-mitosis/a/hs-mitosis",
                ),
            },
        ],
        "chemistry": [
            {
                "prompt": "Balance the chemical equation: {equation}.",
                "answer": "{balanced}",
                "topic": "Chemical equations",
                "skill_focus": "Balancing equations",
                "strategy": "Count atoms on each side and adjust coefficients systematically.",
                "guidance": "Start with elements that appear once on each side.",
                "syllabus": "AQA GCSE Chemistry 4.3.1",
                "resources": (
                    "https://www.bbc.co.uk/bitesize/guides/zckwrdm/revision/3",
                ),
            },
            {
                "prompt": "Describe how ionic bonds are formed between metals and non-metals.",
                "answer": "Electrons transfer from metal to non-metal forming oppositely charged ions.",
                "topic": "Bonding",
                "skill_focus": "Describing ionic bonding",
                "strategy": "Explain electron transfer then electrostatic attraction.",
                "guidance": "Mention group 1/2 metals with group 6/7 non-metals.",
                "syllabus": "AQA GCSE Chemistry 4.2.1",
                "resources": (
                    "https://www.khanacademy.org/science/in-in-class-10-chemistry/x0da7149b7dff83df:chemical-bonding/x0da7149b7dff83df:ionic-bonding/a/what-are-ionic-bonds",
                ),
            },
        ],
        "physics": [
            {
                "prompt": "A car accelerates from {v1} m/s to {v2} m/s in {t} s. Calculate the acceleration.",
                "answer": "Acceleration = {acceleration} m/s^2",
                "topic": "Kinematics",
                "skill_focus": "Applying equations of motion",
                "strategy": "Use a = (v - u) / t with consistent units.",
                "guidance": "State the formula before substituting values.",
                "syllabus": "AQA GCSE Physics 5.1",
                "resources": (
                    "https://www.physicsandmathstutor.com/physics-revision/gcse-aqa/forces/",
                ),
            },
            {
                "prompt": "State Newton's three laws of motion and provide an everyday example for each.",
                "answer": "Inertia, F=ma, action-reaction; examples include seatbelts, pushing trolleys, rocket propulsion.",
                "topic": "Forces",
                "skill_focus": "Explaining Newton's laws",
                "strategy": "State each law clearly then pair with a context.",
                "guidance": "Link the example back to the law's wording.",
                "syllabus": "AQA GCSE Physics 5.4",
                "resources": (
                    "https://www.bbc.co.uk/bitesize/guides/zmwq7hv/revision/1",
                ),
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
            recommended_minutes = max(2, round(marks * 1.5))
            prompt = self._fill_template(template["prompt"], rand)
            answer = self._fill_template(template["answer"], rand)
            notes = self._TIER_HINTS.get(params.tier)
            method_breakdown = self._scaffold_method(template)
            common_pitfalls = self._pitfall_hint(template)
            examiner_notes = self._examiner_note(params, template)
            questions.append(
                GeneratedQuestion(
                    number=number,
                    prompt=prompt,
                    topic=template["topic"],
                    difficulty=params.difficulty.title(),
                    marks=marks,
                    answer=answer,
                    notes=notes,
                    skill_focus=template.get("skill_focus", "Core reasoning"),
                    strategy=template.get("strategy", "Show every step."),
                    guidance=template.get("guidance", "Explain your reasoning."),
                    syllabus_reference=template.get("syllabus", "GCSE specification"),
                    estimated_minutes=recommended_minutes,
                    resources=template.get("resources", ()),
                    method_breakdown=method_breakdown,
                    common_pitfalls=common_pitfalls,
                    examiner_notes=examiner_notes,
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

    def _scaffold_method(self, template: Dict[str, str]) -> str:
        if "strategy" in template:
            return template["strategy"] + " Ensure each stage is justified."
        return "Break the problem into manageable steps and justify your reasoning."

    def _pitfall_hint(self, template: Dict[str, str]) -> str:
        topic = template.get("topic", "")
        if "triangle" in topic.lower():
            return "Do not forget to square the lengths before adding."
        if "equation" in topic.lower():
            return "Keep the equation balanced when manipulating terms."
        if "essay" in topic.lower():
            return "Avoid drifting away from the question focus."
        return "Watch for unit errors and misread keywords."

    def _examiner_note(self, params: GenerationParams, template: Dict[str, str]) -> str:
        difficulty = params.difficulty
        if difficulty == "challenging":
            return "Reward precise terminology and fully developed reasoning."
        if difficulty == "easy":
            return "Encourage attempts that demonstrate the key concept, even if incomplete."
        if "writing" in template.get("topic", "").lower():
            return "Credit structural features and technical accuracy."
        return "Look for clear method communication and annotated working."


class MockMarkSchemeLLM:
    """Generate mark scheme entries derived from question data."""

    def generate(self, questions: Iterable[GeneratedQuestion]) -> List[GeneratedQuestion]:
        return [question for question in questions]
