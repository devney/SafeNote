from pathlib import Path


def test_default_is_markdown(main_window):
    assert main_window._current_is_markdown is True  # type: ignore[attr-defined]
    title = main_window.windowTitle()
    assert "Untitled.md" in title


def test_new_file_resets_state(main_window, tmp_path: Path):
    main_window._current_path = tmp_path / "example.md"  # type: ignore[attr-defined]
    main_window.editor.setPlainText("Hello")
    main_window.editor.document().setModified(True)

    spawned: list[Path | None] = []
    main_window._spawn_window = lambda p: spawned.append(p)  # type: ignore[attr-defined]

    main_window.new_file()

    # New opens a new window and leaves the current document unchanged
    assert spawned == [None]
    assert main_window._current_path == tmp_path / "example.md"  # type: ignore[attr-defined]
    assert main_window.editor.toPlainText() == "Hello"


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


def test_serialize_markdown_source_mode(main_window):
    main_window._current_is_markdown = True  # type: ignore[attr-defined]
    main_window.editor.setMarkdown("**Bold** text")

    main_window._set_view_mode("markdown_mode")  # type: ignore[attr-defined]

    data = main_window._serialize_document()  # type: ignore[attr-defined]
    # In markdown mode we expect to see the raw markers
    assert "**Bold** text" in data


def test_view_mode_round_trip(main_window):
    main_window._current_is_markdown = True  # type: ignore[attr-defined]
    main_window.editor.setMarkdown("# Title\n\nBody")
    original = main_window._serialize_document()  # type: ignore[attr-defined]

    main_window._set_view_mode("markdown_mode")  # type: ignore[attr-defined]
    assert main_window.editor.toPlainText()  # type: ignore[attr-defined]

    main_window._set_view_mode("wysiwyg")  # type: ignore[attr-defined]
    round_tripped = main_window._serialize_document()  # type: ignore[attr-defined]
    assert original == round_tripped


def test_recent_files_capped_and_unique(main_window, tmp_path: Path):
    # Avoid touching the real recent-file storage
    main_window._save_recent_files = lambda: None  # type: ignore[attr-defined]
    main_window._rebuild_recent_menu = lambda: None  # type: ignore[attr-defined]

    paths = [tmp_path / f"file{i}.md" for i in range(7)]
    for p in paths:
        p.write_text("x", encoding="utf-8")
        main_window._add_recent_file(p)  # type: ignore[attr-defined]

    recent = main_window._recent_files  # type: ignore[attr-defined]
    assert len(recent) == 5
    # Most recent should be last one added
    assert recent[0] == paths[-1]


def test_close_file_closes_window(main_window):
    main_window._maybe_save = lambda: True  # type: ignore[attr-defined]

    closed = {"called": False}
    main_window.close = lambda: closed.__setitem__("called", True)  # type: ignore[method-assign]

    main_window.close_file()

    assert closed["called"] is True


def test_should_spawn_for_open_is_false_for_pristine_single_window(main_window):
    # Pristine "Untitled" doc
    main_window._current_path = None  # type: ignore[attr-defined]
    main_window.editor.setPlainText("")
    main_window.editor.document().setModified(False)

    # Force "only window" regardless of test runner widgets
    main_window._is_only_main_window = lambda: True  # type: ignore[attr-defined]

    assert main_window._should_spawn_for_open() is False  # type: ignore[attr-defined]

