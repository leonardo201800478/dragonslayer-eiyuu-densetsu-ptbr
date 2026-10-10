from __future__ import annotations

import pytest

from dragonslayer_ptbr.text.atlas_segmenter import (
    LineKind,
    SegmentKind,
    classify_line,
    classify_segment,
)


def test_japanese_text_with_dictionary_and_line_markers_is_segmented() -> None:
    source = "<DICT 0B>は　宝箱を開けました。<LINE>"

    result = classify_line(source)

    assert result.kind is LineKind.MIXED
    assert [segment.kind for segment in result.segments] == [
        SegmentKind.DICTIONARY_MARKER,
        SegmentKind.TEXT,
        SegmentKind.LINE_MARKER,
    ]
    assert "".join(segment.value for segment in result.segments) == source


def test_hexadecimal_control_bytes_are_preserved_as_tokens() -> None:
    source = "<JMP.L><$FF><$FF><$6E><$2B>"

    result = classify_line(source)

    assert result.kind is LineKind.OTHER
    assert [segment.kind for segment in result.segments] == [
        SegmentKind.CONTROL_FLOW_MARKER,
        SegmentKind.HEX_BYTE,
        SegmentKind.HEX_BYTE,
        SegmentKind.HEX_BYTE,
        SegmentKind.HEX_BYTE,
    ]
    assert "".join(segment.value for segment in result.segments) == source


def test_atlas_directives_are_not_split_or_marked_as_translation_text() -> None:
    source = '#W08BYTE($7B8, $EB, "insert/01_1356A0.bin")'

    result = classify_line(source)

    assert result.kind is LineKind.DIRECTIVE
    assert result.segments == ()
    assert result.raw == source


def test_file_reference_takes_precedence_over_comment_classification() -> None:
    source = "//[FILE] binary//01_1356A0.bin"

    result = classify_line(source)

    assert result.kind is LineKind.FILE_REFERENCE
    assert result.raw == source


def test_comment_with_end_marker_is_not_treated_as_executable_control() -> None:
    source = "//<END 06>"

    result = classify_line(source)

    assert result.kind is LineKind.COMMENT
    assert result.segments == ()


def test_unknown_inline_markers_are_preserved_without_guessing_semantics() -> None:
    source = "<UNKNOWN 12>日本語"

    result = classify_line(source)

    assert result.kind is LineKind.MIXED
    assert result.segments[0].kind is SegmentKind.UNKNOWN_MARKER
    assert result.segments[0].value == "<UNKNOWN 12>"
    assert "".join(segment.value for segment in result.segments) == source


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("<WAIT>", SegmentKind.WAIT_MARKER),
        ("<WAIT CLEAR>", SegmentKind.WAIT_MARKER),
        ("<COLOR OFF>", SegmentKind.COLOR_MARKER),
        ("<COLOR 1E>", SegmentKind.COLOR_MARKER),
        ("<COLOR 1C>", SegmentKind.COLOR_MARKER),
        ("<COLOR 1F>", SegmentKind.COLOR_MARKER),
        ("<HERO 1>", SegmentKind.HERO_MARKER),
        ("<HERO 4>", SegmentKind.HERO_MARKER),
        ("<FLAG 13>", SegmentKind.FLAG_MARKER),
        ("<FLAG 14>", SegmentKind.FLAG_MARKER),
        ("<CODE 0C>", SegmentKind.CODE_MARKER),
        ("<NAME>", SegmentKind.NAME_MARKER),
        ("<JMP 0F>", SegmentKind.CONTROL_FLOW_MARKER),
    ],
)
def test_reported_atlas_markers_have_syntactic_categories(
    token: str, expected: SegmentKind
) -> None:
    assert classify_segment(token) is expected


def test_parameterized_markers_and_bytes_round_trip_without_changes() -> None:
    source = (
        "<COLOR 1E>ナイフ<COLOR OFF><COLOR 1C>を　装備しました。"
        "<CODE 0C><$03><$01><COLOR OFF><WAIT CLEAR>"
    )

    result = classify_line(source)

    assert "".join(segment.value for segment in result.segments) == source
    assert [segment.kind for segment in result.segments if segment.value.startswith("<$")] == [
        SegmentKind.HEX_BYTE,
        SegmentKind.HEX_BYTE,
    ]


def test_plain_japanese_text_is_classified_as_text() -> None:
    source = "宝箱の中には"

    result = classify_line(source)

    assert result.kind is LineKind.TEXT
    assert len(result.segments) == 1
    assert result.segments[0].kind is SegmentKind.TEXT
    assert result.segments[0].value == source


def test_blank_line_is_other_and_preserved() -> None:
    result = classify_line("")

    assert result.kind is LineKind.OTHER
    assert result.raw == ""
    assert result.segments == ()
