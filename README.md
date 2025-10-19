# GCSE Past Paper Generator

An end-to-end demo that produces GCSE-style exam papers and mark schemes from simple parameters. Users provide the subject, exam board, tier, difficulty and number of questions; the app then calls a lightweight LLM stub, renders styled PDFs and presents download links via a polished web interface.

## Features

- **Guided parameter capture** – clean form UI with validation for supported subjects, tiers and exam boards.
- **LLM-ready orchestration** – swap in your preferred LLM provider while keeping prompt/response handling deterministic for tests.
- **Styled PDFs** – ReportLab layouts for both the exam paper and the accompanying mark scheme.
- **Modern frontend** – responsive design, summary tables and quick download actions.
- **Exam logistics** – each question includes total marks, recommended timing, skill focus and specification references.
- **Reflection workflow** – log weaknesses to instantly generate flashcards, summary notes and curated resource links.

## Project layout

```
src/past_paper_generator/
├── __init__.py            # Package exports
├── app.py                 # Flask app and HTTP routes
├── generator.py           # Orchestration service
├── llm_stub.py            # Deterministic question + mark scheme generator
├── pdf.py                 # PDF rendering helpers
├── schemas.py             # Data models and validation
├── static/                # CSS assets
└── templates/             # HTML templates
```

## Getting started

1. **Create and activate a virtual environment** (recommended)

   ```bash
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. **Install dependencies and the app package**

   ```bash
   pip install -r requirements.txt
   ```

   The requirements file installs the project itself in editable mode, so
   the `past_paper_generator` package is importable for both the CLI and
   the Flask runner. If you prefer, you can run `pip install -e .` instead.

3. **Run the development server**

   ```bash
   flask --app past_paper_generator.app --debug run
   ```

   If you prefer to avoid the `flask` CLI, you can launch the app directly:

   ```bash
   python -m past_paper_generator.app
   ```

4. Open <http://127.0.0.1:5000> and generate your first paper.

Generated PDFs are stored inside the `outputs/` directory. Use the download buttons on the result page or access the files directly from disk.

## Customisation

- Replace `MockQuestionLLM` and `MockMarkSchemeLLM` in `generator.py` with API clients that call your chosen LLM provider.
- Update the question templates inside `llm_stub.py` to expand topic coverage or supply real prompt/response examples.
- Adjust typography, colours or layout by editing `static/styles.css` and the templates inside `templates/`.
- Modify `pdf.py` to incorporate branding, logos or multi-column mark schemes.
- Extend `revision.py` to integrate real analytics, progress tracking or spaced-repetition tooling.

## Testing the core service

To exercise the orchestration service without the UI:

```python
from past_paper_generator import GenerationParams, PastPaperService

service = PastPaperService()
params = GenerationParams(
    subject="maths",
    exam_board="aqa",
    tier="foundation",
    difficulty="standard",
    num_questions=5,
)
result = service.generate(params)
print(result.paper_pdf)
print(result.mark_scheme_pdf)
```

This will create two PDFs in the `outputs/` directory using the same logic as the web app.

## License

MIT
