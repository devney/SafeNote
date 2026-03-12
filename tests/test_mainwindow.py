from pathlib import Path


def test_default_is_markdown(main_window):
    assert main_window._current_is_markdown is True  # type: ignore[attr-defined]
    title = main_window.windowTitle()
    assert "Untitled.md" in title


def test_new_file_resets_state(main_window, tmp_path: Path):
    main_window._current_path = tmp_path / "example.md"  # type: ignore[attr-defined]
    main_window.editor.setPlainText("Hello")
    main_window.editor.document().setModified(True)

    main_window.new_file()

    assert main_window._current_path is None  # type: ignore[attr-defined]
    assert main_window.editor.toPlainText() == ""
    assert main_window.editor.document().isModified() is False


def test_serialize_plain_text(main_window):
    main_window._current_is_markdown = False  # type: ignore[attr-defined]
    main_window.editor.setPlainText("Plain text")

    data = main_window._serialize_document()  # type: ignore[attr-defined]
    assert data == "Plain text"


def test_serialize_markdown(main_window):
    main_window._current_is_markdown = True  # type: ignore[attr-defined]
    main_window.editor.setMarkdown("**Bold** text")

    data = main_window._serialize_document()  # type: ignore[attr-defined]
    assert "**Bold**" in data

