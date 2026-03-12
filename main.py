import sys
from pathlib import Path

from PySide6.QtCore import QSignalBlocker
from PySide6.QtGui import QAction, QFont, QFontDatabase, QKeySequence, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
)


APP_NAME = "SafeNote"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._current_path: Path | None = None
        self._current_is_markdown: bool = False

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.setCentralWidget(self.editor)

        self._create_actions()
        self._create_menus()

        self.editor.document().modificationChanged.connect(self._update_window_title)
        self.editor.currentCharFormatChanged.connect(self._sync_format_actions)
        self._update_window_title()

        self.resize(900, 650)

    def _merge_format_on_selection(self, fmt: QTextCharFormat) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _create_actions(self) -> None:
        # Edit actions
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

        # Format actions
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

        # File actions
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

        # Enable/disable wiring
        self.editor.document().undoAvailable.connect(self.action_undo.setEnabled)
        self.editor.document().redoAvailable.connect(self.action_redo.setEnabled)
        self.editor.copyAvailable.connect(self.action_cut.setEnabled)
        self.editor.copyAvailable.connect(self.action_copy.setEnabled)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
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

        font_menu = format_menu.addMenu("&Font")
        font_db = QFontDatabase()
        for family in font_db.families():
            action = QAction(family, self)
            action.triggered.connect(
                lambda checked=False, fam=family: self._set_font_family(fam)
            )
            font_menu.addAction(action)

        size_menu = format_menu.addMenu("Font &Size")
        for size in (8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32):
            action = QAction(f"{size} pt", self)
            action.triggered.connect(
                lambda checked=False, s=size: self._set_font_size(s)
            )
            size_menu.addAction(action)

    def _set_font_family(self, family: str) -> None:
        fmt = QTextCharFormat()
        fmt.setFontFamily(family)
        self._merge_format_on_selection(fmt)

    def _set_font_size(self, size: int) -> None:
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(size))
        self._merge_format_on_selection(fmt)

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

    def _sync_format_actions(self, fmt: QTextCharFormat) -> None:
        with QSignalBlocker(self.action_bold):
            self.action_bold.setChecked(fmt.fontWeight() >= QFont.Weight.Bold)
        with QSignalBlocker(self.action_italic):
            self.action_italic.setChecked(fmt.fontItalic())
        with QSignalBlocker(self.action_underline):
            self.action_underline.setChecked(fmt.fontUnderline())
        with QSignalBlocker(self.action_strikethrough):
            self.action_strikethrough.setChecked(fmt.fontStrikeOut())

    def _update_window_title(self) -> None:
        name = self._current_path.name if self._current_path else (
            "Untitled.md" if self._current_is_markdown else "Untitled.txt"
        )
        modified = "*" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{modified} — {APP_NAME}")

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
        self._current_is_markdown = False
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()

    def close_file(self) -> None:
        if not self._maybe_save():
            return

        self._current_path = None
        self._current_is_markdown = False
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()

    def open_file(self) -> None:
        if not self._maybe_save():
            return

        filename, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Open file",
            str(Path.home()),
            "Text files (*.txt);;Markdown files (*.md);;All files (*.*)",
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

        if is_markdown:
            self.editor.setMarkdown(text)
        else:
            self.editor.setPlainText(text)

        self.editor.document().setModified(False)
        self._update_window_title()

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
            "Text files (*.txt);;Markdown files (*.md);;All files (*.*)",
        )
        if not filename:
            return None, self._current_is_markdown

        path = Path(filename)
        ext = path.suffix.lower()

        if "Markdown files" in selected_filter or ext == ".md":
            if ext != ".md":
                path = path.with_suffix(".md")
            return path, True

        # Default to .txt for everything else
        if ext != ".txt":
            path = path.with_suffix(".txt")
        return path, False

    def _serialize_document(self) -> str:
        if self._current_is_markdown:
            return self.editor.document().toMarkdown()
        return self.editor.toPlainText()

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
        return self.save_file()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API name)
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

import sys
from pathlib import Path

from PySide6.QtCore import QSignalBlocker
from PySide6.QtGui import QAction, QFont, QFontDatabase, QKeySequence, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
)


APP_NAME = "SafeNote"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._current_path: Path | None = None

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.setCentralWidget(self.editor)

        self._create_actions()
        self._create_menus()

        self.editor.document().modificationChanged.connect(self._update_window_title)
        self.editor.currentCharFormatChanged.connect(self._sync_format_actions)
        self._update_window_title()

        self.resize(900, 650)

    def _merge_format_on_selection(self, fmt: QTextCharFormat) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

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

        self.editor.document().undoAvailable.connect(self.action_undo.setEnabled)
        self.editor.document().redoAvailable.connect(self.action_redo.setEnabled)
        self.editor.copyAvailable.connect(self.action_cut.setEnabled)
        self.editor.copyAvailable.connect(self.action_copy.setEnabled)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
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

        font_menu = format_menu.addMenu("&Font")
        font_db = QFontDatabase()
        for family in font_db.families():
            action = QAction(family, self)
            action.triggered.connect(
                lambda checked=False, fam=family: self._set_font_family(fam)
            )
            font_menu.addAction(action)

    def _set_font_family(self, family: str) -> None:
        fmt = QTextCharFormat()
        fmt.setFontFamily(family)
        self._merge_format_on_selection(fmt)

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

    def _sync_format_actions(self, fmt: QTextCharFormat) -> None:
        with QSignalBlocker(self.action_bold):
            self.action_bold.setChecked(fmt.fontWeight() >= QFont.Weight.Bold)
        with QSignalBlocker(self.action_italic):
            self.action_italic.setChecked(fmt.fontItalic())
        with QSignalBlocker(self.action_underline):
            self.action_underline.setChecked(fmt.fontUnderline())
        with QSignalBlocker(self.action_strikethrough):
            self.action_strikethrough.setChecked(fmt.fontStrikeOut())

    def _update_window_title(self) -> None:
        name = self._current_path.name if self._current_path else "Untitled.txt"
        modified = "*" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{modified} — {APP_NAME}")

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
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()

    def close_file(self) -> None:
        if not self._maybe_save():
            return

        self._current_path = None
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()

    def open_file(self) -> None:
        if not self._maybe_save():
            return

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open text file",
            str(Path.home()),
            "Text files (*.txt);;All files (*.*)",
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

        self._current_path = path
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self._update_window_title()

    def _choose_save_path(self) -> Path | None:
        suggested = (
            str(self._current_path)
            if self._current_path
            else str(Path.home() / "Untitled.txt")
        )
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save text file",
            suggested,
            "Text files (*.txt);;All files (*.*)",
        )
        if not filename:
            return None

        path = Path(filename)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        return path

    def save_file(self) -> bool:
        if self._current_path is None:
            return self.save_file_as()

        try:
            self._current_path.write_text(
                self.editor.toPlainText(),
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
        path = self._choose_save_path()
        if path is None:
            return False

        self._current_path = path
        return self.save_file()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API name)
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

import sys
from pathlib import Path

from PySide6.QtCore import QSignalBlocker
from PySide6.QtGui import QAction, QFont, QKeySequence, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
)


APP_NAME = "SafeNote"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._current_path: Path | None = None

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.setCentralWidget(self.editor)

        self._create_actions()
        self._create_menus()

        self.editor.document().modificationChanged.connect(self._update_window_title)
        self.editor.currentCharFormatChanged.connect(self._sync_format_actions)
        self._update_window_title()

        self.resize(900, 650)

    def _merge_format_on_selection(self, fmt: QTextCharFormat) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

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

        self.editor.document().undoAvailable.connect(self.action_undo.setEnabled)
        self.editor.document().redoAvailable.connect(self.action_redo.setEnabled)
        self.editor.copyAvailable.connect(self.action_cut.setEnabled)
        self.editor.copyAvailable.connect(self.action_copy.setEnabled)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
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

    def _sync_format_actions(self, fmt: QTextCharFormat) -> None:
        with QSignalBlocker(self.action_bold):
            self.action_bold.setChecked(fmt.fontWeight() >= QFont.Weight.Bold)
        with QSignalBlocker(self.action_italic):
            self.action_italic.setChecked(fmt.fontItalic())
        with QSignalBlocker(self.action_underline):
            self.action_underline.setChecked(fmt.fontUnderline())
        with QSignalBlocker(self.action_strikethrough):
            self.action_strikethrough.setChecked(fmt.fontStrikeOut())

    def _update_window_title(self) -> None:
        name = self._current_path.name if self._current_path else "Untitled.txt"
        modified = "*" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{modified} — {APP_NAME}")

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
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()

    def close_file(self) -> None:
        if not self._maybe_save():
            return

        self._current_path = None
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()

    def open_file(self) -> None:
        if not self._maybe_save():
            return

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open text file",
            str(Path.home()),
            "Text files (*.txt);;All files (*.*)",
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

        self._current_path = path
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self._update_window_title()

    def _choose_save_path(self) -> Path | None:
        suggested = (
            str(self._current_path)
            if self._current_path
            else str(Path.home() / "Untitled.txt")
        )
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save text file",
            suggested,
            "Text files (*.txt);;All files (*.*)",
        )
        if not filename:
            return None

        path = Path(filename)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        return path

    def save_file(self) -> bool:
        if self._current_path is None:
            return self.save_file_as()

        try:
            self._current_path.write_text(
                self.editor.toPlainText(),
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
        path = self._choose_save_path()
        if path is None:
            return False

        self._current_path = path
        return self.save_file()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API name)
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

import sys
from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
)


APP_NAME = "SafeNote"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._current_path: Path | None = None

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        self.setCentralWidget(self.editor)

        self._create_actions()
        self._create_menus()

        self.editor.document().modificationChanged.connect(self._update_window_title)
        self._update_window_title()

        self.resize(900, 650)

    def _create_actions(self) -> None:
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

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addSeparator()
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.action_close)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

    def _update_window_title(self) -> None:
        name = self._current_path.name if self._current_path else "Untitled.txt"
        modified = "*" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{modified} — {APP_NAME}")

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
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()

    def close_file(self) -> None:
        if not self._maybe_save():
            return

        self._current_path = None
        self.editor.clear()
        self.editor.document().setModified(False)
        self._update_window_title()

    def open_file(self) -> None:
        if not self._maybe_save():
            return

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open text file",
            str(Path.home()),
            "Text files (*.txt);;All files (*.*)",
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

        self._current_path = path
        self.editor.setPlainText(text)
        self.editor.document().setModified(False)
        self._update_window_title()

    def _choose_save_path(self) -> Path | None:
        suggested = (
            str(self._current_path)
            if self._current_path
            else str(Path.home() / "Untitled.txt")
        )
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save text file",
            suggested,
            "Text files (*.txt);;All files (*.*)",
        )
        if not filename:
            return None

        path = Path(filename)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        return path

    def save_file(self) -> bool:
        if self._current_path is None:
            return self.save_file_as()

        try:
            self._current_path.write_text(
                self.editor.toPlainText(),
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
        path = self._choose_save_path()
        if path is None:
            return False

        self._current_path = path
        return self.save_file()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API name)
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
