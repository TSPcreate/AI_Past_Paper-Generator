"""Flask application exposing the GCSE past paper generator."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_file, url_for

from .generator import PastPaperService
from .schemas import (
    ALLOWED_DIFFICULTIES,
    ALLOWED_EXAM_BOARDS,
    ALLOWED_SUBJECTS,
    ALLOWED_TIERS,
    GenerationParams,
    ValidationError,
)

OUTPUT_DIR = Path("outputs")

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)
app.secret_key = "change-me"
service = PastPaperService()


@app.route("/", methods=["GET"])
def index() -> str:
    return render_template(
        "index.html",
        subjects=_choice_pairs(ALLOWED_SUBJECTS),
        exam_boards=_choice_pairs(ALLOWED_EXAM_BOARDS),
        tiers=_choice_pairs(ALLOWED_TIERS),
        difficulties=_choice_pairs(ALLOWED_DIFFICULTIES),
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
    questions = list(bundle.questions)
    mark_scheme = list(bundle.mark_scheme)

    return render_template(
        "result.html",
        bundle=bundle,
        questions=questions,
        mark_scheme=mark_scheme,
        paper_url=url_for("download_file", filename=bundle.paper_pdf.name),
        scheme_url=url_for("download_file", filename=bundle.mark_scheme_pdf.name),
    )


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


if __name__ == "__main__":
    app.run(debug=True)
