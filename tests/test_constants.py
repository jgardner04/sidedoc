"""Tests for alignment constants."""

from docx.enum.text import WD_ALIGN_PARAGRAPH


def test_alignment_maps_are_bidirectional() -> None:
    """Verify string→enum and enum→string mappings are consistent."""
    from sidedoc.constants import (
        ALIGNMENT_STRING_TO_ENUM,
        ALIGNMENT_NUMERIC_TO_STRING,
    )

    # Every string that maps to an enum should have the enum map back
    for alignment_str, enum_val in ALIGNMENT_STRING_TO_ENUM.items():
        # The enum's numeric value should map back to the string
        assert ALIGNMENT_NUMERIC_TO_STRING.get(enum_val.value) == alignment_str, (
            f"Alignment '{alignment_str}' maps to enum {enum_val} (value={enum_val.value}), "
            f"but numeric map has {ALIGNMENT_NUMERIC_TO_STRING.get(enum_val.value)}"
        )


def test_gfm_alignment_roundtrip() -> None:
    """Verify GFM separator conversion is reversible."""
    from sidedoc.constants import (
        GFM_ALIGNMENT_TO_SEPARATOR,
        GFM_SEPARATOR_PATTERNS,
        DEFAULT_ALIGNMENT,
    )

    # Each alignment should produce a separator we can detect
    for alignment in ["left", "center", "right"]:
        separator = GFM_ALIGNMENT_TO_SEPARATOR.get(alignment, "---")

        # Detect alignment from separator using the patterns
        starts_colon = separator.startswith(":")
        ends_colon = separator.endswith(":")

        detected = DEFAULT_ALIGNMENT
        for align, (expected_start, expected_end) in GFM_SEPARATOR_PATTERNS.items():
            if starts_colon == expected_start and ends_colon == expected_end:
                detected = align
                break

        assert detected == alignment, (
            f"Alignment '{alignment}' -> separator '{separator}' -> detected '{detected}'"
        )


def test_alignment_constants_have_all_standard_alignments() -> None:
    """Ensure all standard alignments are covered."""
    from sidedoc.constants import (
        ALIGNMENT_STRING_TO_ENUM,
        ALIGNMENT_NUMERIC_TO_STRING,
    )

    required_alignments = {"left", "center", "right", "justify"}

    assert set(ALIGNMENT_STRING_TO_ENUM.keys()) == required_alignments
    assert set(ALIGNMENT_NUMERIC_TO_STRING.values()) == required_alignments


def test_alignment_enum_values_are_correct() -> None:
    """Verify enum mappings match python-docx values."""
    from sidedoc.constants import ALIGNMENT_STRING_TO_ENUM

    assert ALIGNMENT_STRING_TO_ENUM["left"] == WD_ALIGN_PARAGRAPH.LEFT
    assert ALIGNMENT_STRING_TO_ENUM["center"] == WD_ALIGN_PARAGRAPH.CENTER
    assert ALIGNMENT_STRING_TO_ENUM["right"] == WD_ALIGN_PARAGRAPH.RIGHT
    assert ALIGNMENT_STRING_TO_ENUM["justify"] == WD_ALIGN_PARAGRAPH.JUSTIFY


def test_gfm_separators_are_valid() -> None:
    """Verify GFM separators contain valid characters."""
    from sidedoc.constants import GFM_ALIGNMENT_TO_SEPARATOR

    for alignment, separator in GFM_ALIGNMENT_TO_SEPARATOR.items():
        # All separators should contain only dashes and colons
        valid_chars = set("-:")
        assert all(c in valid_chars for c in separator), (
            f"Separator for '{alignment}' has invalid characters: {separator}"
        )
        # All should have at least 3 dashes
        assert separator.count("-") >= 3, (
            f"Separator for '{alignment}' should have at least 3 dashes: {separator}"
        )
