"""Flask application exposing the GCSE past paper generator."""

from __future__ import annotations

from pathlib import Path

from dataclasses import asdict, dataclass, field
from datetime import datetime

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from .generator import PastPaperService
from .schemas import (
    ALLOWED_DIFFICULTIES,
    ALLOWED_EXAM_BOARDS,
    ALLOWED_SUBJECTS,
    ALLOWED_TIERS,
    GenerationParams,
    PaperBundle,
    StudyMaterials,
    ValidationError,
)
from .study import build_study_materials

OUTPUT_DIR = Path("outputs")

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)
app.secret_key = "change-me"
service = PastPaperService()
BUNDLE_CACHE: dict[str, PaperBundle] = {}
STUDY_CACHE: dict[str, "StudySessionRecord"] = {}


@dataclass(slots=True)
class ReflectionEntry:
    """A captured learner reflection for a study session."""

    text: str
    created: datetime

    @property
    def iso(self) -> str:
        return self.created.isoformat(timespec="seconds")

    @property
    def human(self) -> str:
        return self.created.strftime("%d %b %Y · %H:%M")


@dataclass(slots=True)
class StudySessionRecord:
    """Cached study materials enriched with session metadata."""

    materials: StudyMaterials
    llm_key: str | None = None
    reflections: list[ReflectionEntry] = field(default_factory=list)

    def add_reflection(self, note: str) -> None:
        self.reflections.insert(0, ReflectionEntry(text=note, created=datetime.utcnow()))


@app.route("/", methods=["GET"])
def index() -> str:
    llm_key = session.get("llm_api_key")
    return render_template(
        "index.html",
        subjects=_choice_pairs(ALLOWED_SUBJECTS),
        exam_boards=_choice_pairs(ALLOWED_EXAM_BOARDS),
        tiers=_choice_pairs(ALLOWED_TIERS),
        difficulties=_choice_pairs(ALLOWED_DIFFICULTIES),
        llm_key_tail=_mask_key(llm_key),
    )


@app.route("/generate", methods=["POST"])
def generate() -> str:
    try:
        params = GenerationParams(
            subject=request.form.get("subject", ""),
            exam_board=request.form.get("exam_board", ""),
            tier=request.form.get("tier", ""),
            difficulty=request.form.get("difficulty", ""),
            num_questions=int(request.form.get("num_questions", "0")),
        ).validate()
    except (ValidationError, ValueError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))

    bundle = service.generate(params, output_dir=OUTPUT_DIR)
    BUNDLE_CACHE[bundle.slug] = bundle
    llm_key = request.form.get("llm_api_key", "").strip()
    if llm_key:
        session["llm_api_key"] = llm_key
    else:
        llm_key = session.get("llm_api_key")

    STUDY_CACHE[bundle.slug] = StudySessionRecord(
        materials=build_study_materials(bundle),
        llm_key=llm_key,
    )
    return _render_result(bundle)


@app.route("/flashcards/<slug>")
def flashcards(slug: str) -> str:
    bundle = BUNDLE_CACHE.get(slug)
    record = STUDY_CACHE.get(slug)
    if not bundle or not record:
        flash("That study session has expired. Generate a fresh paper to continue.", "error")
        return redirect(url_for("index"))

    materials = record.materials
    cards = [asdict(card) for card in materials.flashcards]
    topics = sorted({card["topic"] for card in cards})
    difficulties = sorted({card["difficulty"] for card in cards})
    skill_types = sorted({card["skill_type"] for card in cards})

    return render_template(
        "flashcards.html",
        bundle=bundle,
        cards=cards,
        topics=topics,
        difficulties=difficulties,
        skill_types=skill_types,
        llm_key=record.llm_key or session.get("llm_api_key"),
        llm_key_tail=_mask_key(record.llm_key or session.get("llm_api_key")),
    )


@app.route("/notes/<slug>")
def notes(slug: str) -> str:
    bundle = BUNDLE_CACHE.get(slug)
    record = STUDY_CACHE.get(slug)
    if not bundle or not record:
        flash("Notes are unavailable for this session. Generate a new paper to try again.", "error")
        return redirect(url_for("index"))

    return render_template(
        "notes.html",
        bundle=bundle,
        notes=record.materials.notes,
        reflections=record.reflections,
        llm_key=record.llm_key or session.get("llm_api_key"),
        llm_key_tail=_mask_key(record.llm_key or session.get("llm_api_key")),
    )


@app.route("/resources/<slug>")
def resources(slug: str) -> str:
    bundle = BUNDLE_CACHE.get(slug)
    record = STUDY_CACHE.get(slug)
    if not bundle or not record:
        flash("Resources are unavailable for this session. Generate a new paper to try again.", "error")
        return redirect(url_for("index"))

    groups: dict[str, list[dict]] = {}
    for item in record.materials.resources:
        groups.setdefault(item.topic, []).append(asdict(item))

    grouped = [
        {
            "topic": topic,
            "items": sorted(items, key=lambda entry: entry["type"]),
        }
        for topic, items in sorted(groups.items())
    ]

    return render_template(
        "resources.html",
        bundle=bundle,
        groups=grouped,
        llm_key=record.llm_key or session.get("llm_api_key"),
        llm_key_tail=_mask_key(record.llm_key or session.get("llm_api_key")),
    )


@app.route("/reflection/<slug>", methods=["POST"])
def add_reflection(slug: str) -> str:
    bundle = BUNDLE_CACHE.get(slug)
    record = STUDY_CACHE.get(slug)
    if not bundle or not record:
        flash("That study session has expired. Generate a fresh paper to continue.", "error")
        return redirect(url_for("index"))

    note = (request.form.get("reflection", "") or "").strip()
    if not note:
        flash("Reflection notes cannot be empty.", "error")
        return redirect(url_for("notes", slug=slug) + "#reflection-journal")

    record.add_reflection(note)
    flash("Reflection saved.", "success")
    return redirect(url_for("notes", slug=slug) + "#reflection-journal")


@app.route("/download/<path:filename>")
def download_file(filename: str):
    target = (OUTPUT_DIR / filename).resolve()
    root = OUTPUT_DIR.resolve()
    if root not in target.parents:
        abort(404)
    if not target.exists() or not target.is_file():
        abort(404)
    return send_file(target, as_attachment=True)


def _choice_pairs(options: dict[str, str]) -> list[tuple[str, str]]:
    return [(key, label) for key, label in sorted(options.items(), key=lambda item: item[1])]


def _render_result(
    bundle: PaperBundle,
) -> str:
    questions = list(bundle.questions)
    mark_scheme = list(bundle.mark_scheme)
    return render_template(
        "result.html",
        bundle=bundle,
        questions=questions,
        mark_scheme=mark_scheme,
        paper_url=url_for("download_file", filename=bundle.paper_pdf.name),
        scheme_url=url_for("download_file", filename=bundle.mark_scheme_pdf.name),
        llm_key_tail=_mask_key(session.get("llm_api_key")),
    )


if __name__ == "__main__":
    app.run(debug=True)


def _mask_key(value: str | None) -> str:
    if not value:
        return ""
    trimmed = value.strip()
    if len(trimmed) <= 4:
        return trimmed
    return trimmed[-4:]
