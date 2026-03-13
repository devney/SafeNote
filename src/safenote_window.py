import json
import sys
from pathlib import Path

from PySide6.QtCore import QSignalBlocker
from PySide6.QtGui import QAction, QFont, QKeySequence, QTextCharFormat, QTextOption
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
    QLabel,
)


APP_NAME = "SafeNote"


class PlainPasteTextEdit(QTextEdit):
    """Text edit that always pastes plain text only (no colors, fonts, or other formatting)."""

    def insertFromMimeData(self, source) -> None:
        if source.hasText():
            self.insertPlainText(source.text())
        # Ignore HTML and other formatted content so pasted text is always unformatted


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._current_path: Path | None = None
        self._current_is_markdown: bool = True
        self._view_mode: str = "wysiwyg"
        self._recent_files: list[Path] = []

        self.editor = PlainPasteTextEdit()
        self.editor.setAcceptRichText(True)
        self.setCentralWidget(self.editor)

        self._create_actions()
        self._create_menus()

        self._load_recent_files()
        self._rebuild_recent_menu()

        self._status_label = QLabel()
        self.statusBar().addPermanentWidget(self._status_label)

        self._base_font = self.editor.font()

        # Ensure markdown headings render with distinct sizes in WYSIWYG
        self.editor.document().setDefaultStyleSheet("""
            h1 { font-size: 22pt; font-weight: bold; }
            h2 { font-size: 18pt; font-weight: bold; }
            h3 { font-size: 14pt; font-weight: bold; }
            h4 { font-size: 12pt; font-weight: bold; }
            h5 { font-size: 11pt; font-weight: bold; }
            h6 { font-size: 10pt; font-weight: bold; }
        """)

        self.editor.document().modificationChanged.connect(self._update_window_title)
        self.editor.currentCharFormatChanged.connect(self._sync_format_actions)
        self.editor.cursorPositionChanged.connect(self._update_status_bar)
        self._update_window_title()
        self._update_status_bar()

        self.resize(900, 650)

    def _merge_format_on_selection(self, fmt: QTextCharFormat) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_bold(self, checked: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._merge_format_on_selection(fmt)

    def _toggle_italic(self, checked: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._merge_format_on_selection(fmt)

    def _toggle_underline(self, checked: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(checked)
        self._merge_format_on_selection(fmt)

    def _toggle_strikethrough(self, checked: bool) -> None:
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(checked)
        self._merge_format_on_selection(fmt)

    # Markdown helpers
    def _wrap_selection(self, prefix: str, suffix: str) -> None:
        cursor = self.editor.textCursor()
        text = cursor.selectedText()
        if not text:
            cursor.insertText(prefix + suffix)
            cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.MoveAnchor, len(suffix))
            self.editor.setTextCursor(cursor)
            return
        cursor.insertText(prefix + text + suffix)

    def _insert_block_prefix(self, prefix: str) -> None:
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        if not cursor.hasSelection():
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.insertText(prefix)
        else:
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            while cursor.position() <= end:
                cursor.movePosition(cursor.MoveOperation.StartOfLine)
                cursor.insertText(prefix)
                if not cursor.movePosition(cursor.MoveOperation.Down):
                    break
                if cursor.position() > end:
                    break
        cursor.endEditBlock()

    def _sync_format_actions(self, fmt: QTextCharFormat) -> None:
        with QSignalBlocker(self.action_bold):
            self.action_bold.setChecked(fmt.fontWeight() >= QFont.Weight.Bold)
        with QSignalBlocker(self.action_italic):
            self.action_italic.setChecked(fmt.fontItalic())
        with QSignalBlocker(self.action_underline):
            self.action_underline.setChecked(fmt.fontUnderline())
        with QSignalBlocker(self.action_strikethrough):
            self.action_strikethrough.setChecked(fmt.fontStrikeOut())

    def _create_actions(self) -> None:
        self.action_undo = QAction("&Undo", self)
        self.action_undo.setShortcut(QKeySequence.Undo)
        self.action_undo.setEnabled(False)
        self.action_undo.triggered.connect(self.editor.undo)

        self.action_redo = QAction("&Redo", self)
        self.action_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self.action_redo.setEnabled(False)
        self.action_redo.triggered.connect(self.editor.redo)

        self.action_cut = QAction("Cu&t", self)
        self.action_cut.setShortcut(QKeySequence.Cut)
        self.action_cut.setEnabled(False)
        self.action_cut.triggered.connect(self.editor.cut)

        self.action_copy = QAction("&Copy", self)
        self.action_copy.setShortcut(QKeySequence.Copy)
        self.action_copy.setEnabled(False)
        self.action_copy.triggered.connect(self.editor.copy)

        self.action_paste = QAction("&Paste", self)
        self.action_paste.setShortcut(QKeySequence.Paste)
        self.action_paste.triggered.connect(self.editor.paste)

        self.action_select_all = QAction("Select &All", self)
        self.action_select_all.setShortcut(QKeySequence.SelectAll)
        self.action_select_all.triggered.connect(self.editor.selectAll)

        self.action_bold = QAction("&Bold", self)
        self.action_bold.setCheckable(True)
        self.action_bold.setShortcut(QKeySequence.Bold)
        self.action_bold.toggled.connect(self._toggle_bold)

        self.action_italic = QAction("&Italic", self)
        self.action_italic.setCheckable(True)
        self.action_italic.setShortcut(QKeySequence.Italic)
        self.action_italic.toggled.connect(self._toggle_italic)

        self.action_underline = QAction("&Underline", self)
        self.action_underline.setCheckable(True)
        self.action_underline.setShortcut(QKeySequence.Underline)
        self.action_underline.toggled.connect(self._toggle_underline)

        self.action_strikethrough = QAction("&Strikethrough", self)
        self.action_strikethrough.setCheckable(True)
        self.action_strikethrough.toggled.connect(self._toggle_strikethrough)

        # Insert / Markdown actions
        self.action_heading1 = QAction("Heading &1", self)
        self.action_heading1.triggered.connect(lambda: self._insert_block_prefix("# "))

        self.action_heading2 = QAction("Heading &2", self)
        self.action_heading2.triggered.connect(lambda: self._insert_block_prefix("## "))

        self.action_heading3 = QAction("Heading &3", self)
        self.action_heading3.triggered.connect(lambda: self._insert_block_prefix("### "))

        self.action_bullet_list = QAction("&Bulleted list", self)
        self.action_bullet_list.triggered.connect(lambda: self._insert_block_prefix("- "))

        self.action_numbered_list = QAction("&Numbered list", self)
        self.action_numbered_list.triggered.connect(lambda: self._insert_block_prefix("1. "))

        self.action_inline_code = QAction("Inline &code", self)
        self.action_inline_code.triggered.connect(lambda: self._wrap_selection("`", "`"))

        self.action_code_block = QAction("&Code block", self)
        self.action_code_block.triggered.connect(self._insert_code_block)

        self.action_blockquote = QAction("&Block quote", self)
        self.action_blockquote.triggered.connect(lambda: self._insert_block_prefix("> "))

        self.action_horizontal_rule = QAction("Horizontal &rule", self)
        self.action_horizontal_rule.triggered.connect(self._insert_horizontal_rule)

        self.action_link = QAction("&Link", self)
        self.action_link.triggered.connect(self._insert_link)

        self.action_image = QAction("&Image", self)
        self.action_image.triggered.connect(self._insert_image)

        # View actions
        self.action_toggle_word_wrap = QAction("Word &Wrap", self)
        self.action_toggle_word_wrap.setCheckable(True)
        self.action_toggle_word_wrap.setChecked(True)
        self.action_toggle_word_wrap.triggered.connect(self._toggle_word_wrap)

        self.action_toggle_whitespace = QAction("Show &Whitespace", self)
        self.action_toggle_whitespace.setCheckable(True)
        self.action_toggle_whitespace.setChecked(False)
        self.action_toggle_whitespace.triggered.connect(self._toggle_whitespace)

        self.action_zoom_in = QAction("Zoom &In", self)
        self.action_zoom_in.setShortcut(QKeySequence.ZoomIn)
        self.action_zoom_in.triggered.connect(lambda: self.editor.zoomIn(1))

        self.action_zoom_out = QAction("Zoom &Out", self)
        self.action_zoom_out.setShortcut(QKeySequence.ZoomOut)
        self.action_zoom_out.triggered.connect(lambda: self.editor.zoomOut(1))

        self.action_zoom_reset = QAction("Reset &Zoom", self)
        self.action_zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        self.action_zoom_reset.triggered.connect(self._reset_zoom)

        self.action_toggle_status_bar = QAction("&Status Bar", self)
        self.action_toggle_status_bar.setCheckable(True)
        self.action_toggle_status_bar.setChecked(True)
        self.action_toggle_status_bar.triggered.connect(self._toggle_status_bar)

        self.action_view_wysiwyg = QAction("&WYSIWYG Mode", self)
        self.action_view_wysiwyg.setCheckable(True)
        self.action_view_wysiwyg.setChecked(True)
        self.action_view_wysiwyg.triggered.connect(
            lambda checked: checked and self._set_view_mode("wysiwyg")
        )

        self.action_view_markdown_mode = QAction("Markdown &Mode", self)
        self.action_view_markdown_mode.setCheckable(True)
        self.action_view_markdown_mode.setChecked(False)
        self.action_view_markdown_mode.triggered.connect(
            lambda checked: checked and self._set_view_mode("markdown_mode")
        )

        self.action_new = QAction("&New", self)
        self.action_new.setShortcut(QKeySequence.New)
        self.action_new.triggered.connect(self.new_file)

        self.action_open = QAction("&Open…", self)
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_open.triggered.connect(self.open_file)

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut(QKeySequence.Save)
        self.action_save.triggered.connect(self.save_file)

        self.action_save_as = QAction("Save &As…", self)
        self.action_save_as.setShortcut(QKeySequence.SaveAs)
        self.action_save_as.triggered.connect(self.save_file_as)

        self.action_close = QAction("&Close File", self)
        self.action_close.setShortcut(QKeySequence.Close)
        self.action_close.triggered.connect(self.close_file)

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut(QKeySequence.Quit)
        self.action_exit.triggered.connect(self.close)

        # Recent-file actions (menu is built dynamically)
        self._recent_menu = None

        self.editor.document().undoAvailable.connect(self.action_undo.setEnabled)
        self.editor.document().redoAvailable.connect(self.action_redo.setEnabled)
        self.editor.copyAvailable.connect(self.action_cut.setEnabled)
        self.editor.copyAvailable.connect(self.action_copy.setEnabled)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        self._recent_menu = file_menu.addMenu("Open &Recent")
        file_menu.addSeparator()
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.action_close)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.action_undo)
        edit_menu.addAction(self.action_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_cut)
        edit_menu.addAction(self.action_copy)
        edit_menu.addAction(self.action_paste)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_select_all)

        format_menu = self.menuBar().addMenu("F&ormat")
        format_menu.addAction(self.action_bold)
        format_menu.addAction(self.action_italic)
        format_menu.addAction(self.action_underline)
        format_menu.addAction(self.action_strikethrough)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.action_view_wysiwyg)
        view_menu.addAction(self.action_view_markdown_mode)
        view_menu.addSeparator()
        view_menu.addAction(self.action_toggle_word_wrap)
        view_menu.addAction(self.action_toggle_whitespace)
        view_menu.addSeparator()
        view_menu.addAction(self.action_zoom_in)
        view_menu.addAction(self.action_zoom_out)
        view_menu.addAction(self.action_zoom_reset)
        view_menu.addSeparator()
        view_menu.addAction(self.action_toggle_status_bar)

        insert_menu = self.menuBar().addMenu("&Insert")
        insert_menu.addAction(self.action_heading1)
        insert_menu.addAction(self.action_heading2)
        insert_menu.addAction(self.action_heading3)
        insert_menu.addSeparator()
        insert_menu.addAction(self.action_bullet_list)
        insert_menu.addAction(self.action_numbered_list)
        insert_menu.addSeparator()
        insert_menu.addAction(self.action_inline_code)
        insert_menu.addAction(self.action_code_block)
        insert_menu.addSeparator()
        insert_menu.addAction(self.action_link)
        insert_menu.addAction(self.action_image)
        insert_menu.addSeparator()
        insert_menu.addAction(self.action_blockquote)
        insert_menu.addAction(self.action_horizontal_rule)

    def _update_window_title(self) -> None:
        name = self._current_path.name if self._current_path else (
            "Untitled.md" if self._current_is_markdown else "Untitled.txt"
        )
        modified = "*" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{modified} — {APP_NAME}")

    def _update_status_bar(self) -> None:
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        mode = "Markdown" if self._current_is_markdown else "Text"
        self._status_label.setText(f"Ln {line}, Col {col}   [{mode}]")

    # Recent files
    @staticmethod
    def _recent_storage_path() -> Path:
        return Path.home() / ".safenote_recent.json"

    def _load_recent_files(self) -> None:
        path = self._recent_storage_path()
        if not path.exists():
            self._recent_files = []
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._recent_files = [Path(p) for p in data if Path(p).exists()]
        except Exception:
            self._recent_files = []

    def _save_recent_files(self) -> None:
        path = self._recent_storage_path()
        try:
            path.write_text(
                json.dumps([str(p) for p in self._recent_files[:5]]),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _add_recent_file(self, path: Path) -> None:
        try:
            path = path.resolve()
        except Exception:
            return
        self._recent_files = [p for p in self._recent_files if p != path]
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:5]
        self._save_recent_files()
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self) -> None:
        if self._recent_menu is None:
            return
        self._recent_menu.clear()
        if not self._recent_files:
            empty_action = QAction("(No recent files)", self)
            empty_action.setEnabled(False)
            self._recent_menu.addAction(empty_action)
            return
        for path in self._recent_files:
            action = QAction(str(path), self)
            action.triggered.connect(
                lambda checked=False, p=path: self._open_recent_file(p)
            )
            self._recent_menu.addAction(action)

    def _open_recent_file(self, path: Path) -> None:
        if not path.exists():
            QMessageBox.warning(
                self,
                APP_NAME,
                f"File not found:\n{path}\n\nIt will be removed from the recent list.",
            )
            self._recent_files = [p for p in self._recent_files if p != path]
            self._save_recent_files()
            self._rebuild_recent_menu()
            return
        if not self._maybe_save():
            return
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            QMessageBox.critical(self, APP_NAME, f"Could not open file:\n{e}")
            return
        is_markdown = path.suffix.lower() == ".md"
        self._current_path = path
        self._current_is_markdown = is_markdown
        if self._view_mode == "wysiwyg" and is_markdown:
            self.editor.setMarkdown(text)
            self.editor.setHtml(self.editor.document().toHtml())
        else:
            self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self._update_window_title()
        self._update_status_bar()

    def _maybe_save(self) -> bool:
        if not self.editor.document().isModified():
            return True

        result = QMessageBox.question(
            self,
            APP_NAME,
            "You have unsaved changes. Save them?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if result == QMessageBox.StandardButton.Cancel:
            return False
        if result == QMessageBox.StandardButton.Discard:
            return True
        return self.save_file()

    def new_file(self) -> None:
        if not self._maybe_save():
            return

        self._current_path = None
        self._current_is_markdown = True
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()
        self._update_status_bar()

    def close_file(self) -> None:
        if not self._maybe_save():
            return

        self._current_path = None
        self._current_is_markdown = True
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()
        self._update_status_bar()

    def open_file(self) -> None:
        if not self._maybe_save():
            return

        filename, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Open file",
            str(Path.home()),
            "All supported files (*.md *.txt);;Markdown files (*.md);;Text files (*.txt);;All files (*.*)",
        )
        if not filename:
            return

        path = Path(filename)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            QMessageBox.critical(self, APP_NAME, f"Could not open file:\n{e}")
            return

        is_markdown = path.suffix.lower() == ".md"
        self._current_path = path
        self._current_is_markdown = is_markdown

        if self._view_mode == "wysiwyg" and is_markdown:
            self.editor.setMarkdown(text)
            self.editor.setHtml(self.editor.document().toHtml())
        else:
            self.editor.setPlainText(text)

        self.editor.document().setModified(False)
        self._update_window_title()
        self._update_status_bar()
        self._add_recent_file(path)

    def _choose_save_path(self) -> tuple[Path | None, bool]:
        suggested_name = (
            str(self._current_path)
            if self._current_path
            else str(
                Path.home()
                / ("Untitled.md" if self._current_is_markdown else "Untitled.txt")
            )
        )

        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save file",
            suggested_name,
            "Markdown files (*.md);;Text files (*.txt);;All files (*.*)",
        )
        if not filename:
            return None, self._current_is_markdown

        path = Path(filename)
        ext = path.suffix.lower()

        if "Markdown files" in selected_filter or ext == ".md":
            if ext != ".md":
                path = path.with_suffix(".md")
            return path, True

        if ext != ".txt":
            path = path.with_suffix(".txt")
        return path, False

    def _serialize_document(self) -> str:
        if self._current_is_markdown:
            if self._view_mode == "wysiwyg":
                return self.editor.document().toMarkdown()
            return self.editor.toPlainText()
        return self.editor.toPlainText()

    # Insert handlers
    def _insert_code_block(self) -> None:
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.insertText("\n```text\n")
        cursor.insertText("\n```\n")
        cursor.movePosition(cursor.MoveOperation.Up)
        self.editor.setTextCursor(cursor)
        cursor.endEditBlock()

    def _insert_horizontal_rule(self) -> None:
        cursor = self.editor.textCursor()
        cursor.insertText("\n---\n")

    def _insert_link(self) -> None:
        cursor = self.editor.textCursor()
        text = cursor.selectedText() or "link text"
        cursor.insertText(f"[{text}](url)")

    def _insert_image(self) -> None:
        cursor = self.editor.textCursor()
        cursor.insertText("![alt text](path/to/image.png)")

    # View handlers
    def _set_view_mode(self, mode: str) -> None:
        if mode == self._view_mode:
            return

        # Capture current markdown/plain-text representation
        if self._current_is_markdown and self._view_mode == "wysiwyg":
            md = self.editor.document().toMarkdown()
        else:
            md = self.editor.toPlainText()

        self._view_mode = mode

        if mode == "markdown_mode":
            self.editor.setAcceptRichText(False)
            self.editor.setPlainText(md)
            with QSignalBlocker(self.action_view_markdown_mode):
                self.action_view_markdown_mode.setChecked(True)
            with QSignalBlocker(self.action_view_wysiwyg):
                self.action_view_wysiwyg.setChecked(False)
        else:
            self.editor.setAcceptRichText(True)
            if self._current_is_markdown:
                self.editor.setMarkdown(md)
                # Re-apply content as HTML so defaultStyleSheet (h1/h2/h3 sizes) is applied
                self.editor.setHtml(self.editor.document().toHtml())
            else:
                self.editor.setPlainText(md)
            with QSignalBlocker(self.action_view_wysiwyg):
                self.action_view_wysiwyg.setChecked(True)
            with QSignalBlocker(self.action_view_markdown_mode):
                self.action_view_markdown_mode.setChecked(False)

    def _toggle_word_wrap(self, checked: bool) -> None:
        mode = QTextEdit.LineWrapMode.WidgetWidth if checked else QTextEdit.LineWrapMode.NoWrap
        self.editor.setLineWrapMode(mode)

    def _toggle_whitespace(self, checked: bool) -> None:
        opt = self.editor.document().defaultTextOption()
        flags = opt.flags()
        if checked:
            flags |= QTextOption.Flag.ShowTabsAndSpaces
        else:
            flags &= ~QTextOption.Flag.ShowTabsAndSpaces
        opt.setFlags(flags)
        self.editor.document().setDefaultTextOption(opt)

    def _reset_zoom(self) -> None:
        self.editor.setFont(self._base_font)

    def _toggle_status_bar(self, checked: bool) -> None:
        self.statusBar().setVisible(checked)

    def save_file(self) -> bool:
        if self._current_path is None:
            return self.save_file_as()

        try:
            data = self._serialize_document()
            self._current_path.write_text(
                data,
                encoding="utf-8",
                newline="",
            )
        except OSError as e:
            QMessageBox.critical(self, APP_NAME, f"Could not save file:\n{e}")
            return False

        self.editor.document().setModified(False)
        self._update_window_title()
        return True

    def save_file_as(self) -> bool:
        path, is_markdown = self._choose_save_path()
        if path is None:
            return False

        self._current_path = path
        self._current_is_markdown = is_markdown
        ok = self.save_file()
        if ok and self._current_path is not None:
            self._add_recent_file(self._current_path)
        return ok

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(True)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

