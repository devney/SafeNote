# SafeNote

Simple cross-platform notepad built with Python and PySide6.

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
  - **WYSIWYG** or **Markdown Mode** (rendered vs raw Markdown)
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

