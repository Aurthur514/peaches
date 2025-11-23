Task 3 — GLR Pipeline (Streamlit)

Overview
--------
This Streamlit app automates filling an insurance template (.docx) using text
extracted from photo report PDFs and an LLM to map template fields to values.

Files added
-----------
- `task_3_glr_streamlit.py` — the Streamlit application
- `task_3_requirements.txt` — Python packages needed for the app
- `task_3_README.md` — this file

Quick start
-----------
1. Create / activate your virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r task_3_requirements.txt
```

2. Set an LLM API key (OpenRouter preferred) in your environment. Example (PowerShell):

```powershell
$env:OPENROUTER_API_KEY = 'sk-...'
# or
$env:OPENAI_API_KEY = 'sk-...'
```

If you have a Google Gemini / Generative Language API key, you can set it as:

```powershell
$env:GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE'
```

The app will prefer `GEMINI_API_KEY` if present, then `OPENROUTER_API_KEY`, then `OPENAI_API_KEY`.

OCR support
-----------
This version adds OCR fallback for scanned photo-report PDFs using `pytesseract` and `pdf2image`.

Requirements (native binaries):
- Tesseract OCR (executable). On Windows you can install via Chocolatey:

```powershell
choco install tesseract
```

- Poppler utilities (required by `pdf2image` to convert PDF pages to images). On Windows, download Poppler for Windows and set `POPPLER_PATH` to the folder containing `pdftoppm.exe`.

Example (PowerShell) if Poppler is installed at `C:\poppler-23.05.0\Library\bin`:

```powershell
$env:POPPLER_PATH = 'C:\poppler-23.05.0\Library\bin'
```

Python packages (already added to `task_3_requirements.txt`):
```text
pdf2image
pytesseract
Pillow
```

If OCR binaries are not present, the app will still attempt text extraction via `PyPDF2` and will skip OCR with a warning.

3. Run Streamlit:

```powershell
streamlit run task_3_glr_streamlit.py
```

Usage notes
-----------
- Template placeholders: The app expects placeholders of the form `{{field_name}}` in
  the `.docx`. If none are present, the app will ask the LLM to propose fields
  based on the template content.
- The app sends the template text and the combined PDF report text to an LLM to
  extract the best-fit values for each field. The mapping is shown in the UI and
  is editable before writing the final `.docx`.
- The app supports OpenRouter (`OPENROUTER_API_KEY`) and OpenAI (`OPENAI_API_KEY`) APIs.

Security & costs
----------------
- LLM calls require network access and API keys. Be mindful of costs and data
  privacy when sending sensitive report content.

Extending
---------
- You can add OCR (Tesseract/pytesseract) if some reports are scans rather than
  searchable PDFs.
- Support for document content controls (Word form fields) can be added to
  better integrate with templates made using Word form controls.
