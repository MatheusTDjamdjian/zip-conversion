"""Testes da camada de CLI e do orquestrador."""

from __future__ import annotations

from pathlib import Path

import pytest

from converter.cli import build_parser, run
from converter.converters import ConversionOptions, ImageConverter
from converter.core import ConversionEngine, build_default_engine
from converter.exceptions import (
    BatchDirectoryError,
    InputFileNotFoundError,
    UnsupportedFormatError,
)
from converter.utils import parse_resize


def test_parser_help_lists_examples() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "--batch" in help_text
    assert "--quality" in help_text
    assert "--resize" in help_text


def test_parse_resize_valid() -> None:
    assert parse_resize("1920x1080") == (1920, 1080)
    assert parse_resize("100X200") == (100, 200)


@pytest.mark.parametrize("invalid", ["abc", "100", "0x10", "-1x10", "100x"])
def test_parse_resize_invalid(invalid: str) -> None:
    with pytest.raises(ValueError):
        parse_resize(invalid)


def test_engine_finds_converter() -> None:
    engine = build_default_engine()
    conv = engine.find_converter("png", "jpg")
    assert conv.supports("png", "jpg")


def test_engine_unsupported_combo_raises() -> None:
    engine = build_default_engine()
    with pytest.raises(UnsupportedFormatError):
        engine.find_converter("xyz", "abc")


def test_engine_supported_sources_and_targets() -> None:
    engine = build_default_engine()
    sources = engine.supported_sources()
    targets = engine.supported_targets()
    assert {"png", "jpg", "webp", "pdf", "txt", "docx"}.issubset(sources)
    assert {"pdf", "png", "jpg", "webp"}.issubset(targets)


def test_run_single_success(sample_png: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.webp"
    code = run([str(sample_png), str(out), "--quiet"])
    assert code == 0
    assert out.exists()


def test_run_missing_args_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        run([])


def test_run_invalid_quality_exits(sample_png: Path, tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run([str(sample_png), str(tmp_path / "x.jpg"), "--quality", "200"])


def test_run_invalid_resize_exits(sample_png: Path, tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run([str(sample_png), str(tmp_path / "x.jpg"), "--resize", "bad"])


def test_run_file_not_found_returns_one(tmp_path: Path) -> None:
    code = run([str(tmp_path / "missing.png"), str(tmp_path / "out.jpg"), "--quiet"])
    assert code == 1


def test_run_unsupported_combo_returns_one(sample_png: Path, tmp_path: Path) -> None:
    code = run([str(sample_png), str(tmp_path / "out.docx"), "--quiet"])
    assert code == 1


def test_run_list_formats(capsys: pytest.CaptureFixture[str]) -> None:
    code = run(["--list-formats"])
    assert code == 0
    captured = capsys.readouterr()
    assert "png" in captured.out
    assert "pdf" in captured.out


def test_run_verbose_and_quiet_conflict(sample_png: Path, tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        run([str(sample_png), str(tmp_path / "x.jpg"), "--verbose", "--quiet"])


def test_run_batch_converts_pngs(tmp_path: Path) -> None:
    from PIL import Image

    src = tmp_path / "in"
    dst = tmp_path / "out"
    src.mkdir()
    for index in range(3):
        Image.new("RGB", (4, 4), color=(index * 60, 100, 50)).save(src / f"img_{index}.png")
    code = run(
        [
            str(src),
            str(dst),
            "--batch",
            "--to",
            "webp",
            "--quiet",
        ]
    )
    assert code == 0
    assert sorted(p.name for p in dst.iterdir()) == [
        "img_0.webp",
        "img_1.webp",
        "img_2.webp",
    ]


def test_run_batch_skips_unsupported(tmp_path: Path) -> None:
    from PIL import Image

    src = tmp_path / "mix"
    dst = tmp_path / "out"
    src.mkdir()
    Image.new("RGB", (4, 4), color="red").save(src / "ok.png")
    (src / "ignore.xyz").write_text("nope")

    code = run(
        [
            str(src),
            str(dst),
            "--batch",
            "--to",
            "jpg",
            "--quiet",
        ]
    )
    assert code == 0
    assert (dst / "ok.jpg").exists()
    assert not (dst / "ignore.jpg").exists()


def test_run_batch_requires_to_format(tmp_path: Path) -> None:
    src = tmp_path / "in"
    dst = tmp_path / "out"
    src.mkdir()
    with pytest.raises(SystemExit):
        run([str(src), str(dst), "--batch", "--quiet"])


def test_run_batch_same_source_and_target_fails(tmp_path: Path) -> None:
    src = tmp_path / "same"
    src.mkdir()
    code = run([str(src), str(src), "--batch", "--to", "png", "--quiet"])
    assert code == 1


def test_engine_convert_file_input_missing(tmp_path: Path) -> None:
    engine = build_default_engine()
    with pytest.raises(InputFileNotFoundError):
        engine.convert_file(tmp_path / "x.png", tmp_path / "y.jpg")


def test_register_custom_converter() -> None:
    engine = ConversionEngine()
    engine.register(ImageConverter())
    assert engine.find_converter("png", "jpg") is not None


def test_options_defaults() -> None:
    options = ConversionOptions()
    assert options.quality == 85
    assert options.resize is None
    assert options.overwrite is True


def test_batch_empty_directory(tmp_path: Path) -> None:
    engine = build_default_engine()
    src = tmp_path / "empty"
    dst = tmp_path / "out"
    src.mkdir()
    result = engine.convert_batch(src, dst, "png", show_progress=False)
    assert result.total == 0
    assert result.converted == 0


def test_batch_directory_error_for_same_paths(tmp_path: Path) -> None:
    engine = build_default_engine()
    same = tmp_path / "same"
    same.mkdir()
    with pytest.raises(BatchDirectoryError):
        engine.convert_batch(same, same, "png", show_progress=False)
