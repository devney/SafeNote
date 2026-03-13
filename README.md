# SafeNote

Simple cross-platform notepad built with Python and PySide6.


## Why “SafeNote”?

SafeNote is designed to be a **convenient, local scratchpad for sensitive information**, not a cloud‑synced notebook:

- **No auto‑save**: content lives in memory only. Unless you explicitly save a file, closing the window discards everything. This makes it safe for short‑lived notes or secrets you do not want written to disk by accident.
- **No AI / network calls**: SafeNote does not embed any AI helpers or call out to external services. Whatever personally identifiable information (PII) or passwords you paste into SafeNote stay on your machine and are **never** sent off to train or query any AI.

A common use case is **temporary password staging** while you build or test a workflow:

- Your long‑term source of truth is a password manager such as Cerberus.
- The password manager (correctly) hides the secret every few minutes and forces a fresh login periodically.
- During intensive testing, you might need to paste the same password dozens of times in a short window (for example, 60 times over 90 minutes).

In that situation, you can copy the password once from Cerberus into SafeNote and use SafeNote as the short‑term copy‑and‑paste source. When you are finished, close the SafeNote window (without saving) and the password is gone from the application along with the rest of its in‑memory contents.


## Features

- New / Open / Save / Save As / Close
- **Markdown-first**: works with plain text (`.txt`) and Markdown (`.md`)
- Standard editing: Undo/Redo, Cut/Copy/Paste, Select All
- Formatting: bold, italic, underline, strikethrough
- Insert helpers:
  - Headings (H1–H3)
  - Bulleted and numbered lists
  - Inline code and fenced code blocks
  - Links, images, block quotes, horizontal rules
- View options:
  - **WYSIWYG** (rendered) or **Markdown** (raw source)
  - Toggle word wrap
  - Zoom in/out/reset
  - Show/hide whitespace
  - Status bar with line/column and mode (Markdown/Text)
- Paste is **always plain text** (no colors/fonts brought in from other apps)
- Recent files: File → Open Recent (last 5 files), persisted across runs


## Running (Windows, PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.main
```


## Running (bash / Git Bash)

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python -m src.main
```


## Building a Windows `.exe` (double-click to run)

This creates a standard Windows executable at `dist\SafeNote.exe` (no console window).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe .\tools\make_icon.py
.\.venv\Scripts\python.exe -m PyInstaller --noconsole --name SafeNote --clean --onefile --icon .\assets\SafeNote.ico .\safenote.py
```

Or run the included build script:

```powershell
.\build.ps1
```


## Building a macOS `.app` (double-click to run)

On macOS, this creates a standard app bundle at `dist/SafeNote.app`:

```bash
chmod +x build_mac.sh
./build_mac.sh
```

