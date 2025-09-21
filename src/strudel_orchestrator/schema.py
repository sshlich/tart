"""Validation helpers for Strudel track metadata and pattern code."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GAIN_PATTERN = re.compile(r"\.gain\(\s*([-+]?[0-9]*\.?[0-9]+)\s*\)")


def validate_metadata(metadata: Dict[str, object] | None) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if metadata is None or not isinstance(metadata, dict):
        errors.append("Metadata block is missing or malformed.")
        return errors, warnings

    slug = metadata.get("slug")
    title = metadata.get("title")
    tempo = metadata.get("tempo")
    mood = metadata.get("mood")
    tags = metadata.get("tags")
    summary = metadata.get("summary")

    if not slug:
        errors.append("`slug` is required.")
    elif not isinstance(slug, str) or not SLUG_PATTERN.match(slug):
        errors.append("`slug` must be kebab-case (lowercase alphanumerics separated by dashes).")

    if not isinstance(title, str) or not title.strip():
        errors.append("`title` must be a non-empty string.")

    if tempo is None:
        errors.append("`tempo` (cycles per minute) is required.")
    else:
        try:
            tempo_value = float(tempo)
            if tempo_value <= 0:
                errors.append("`tempo` must be a positive number.")
            elif not tempo_value.is_integer():
                warnings.append("`tempo` should normally be an integer.")
        except (TypeError, ValueError):
            errors.append("`tempo` must be numeric.")

    if not isinstance(mood, str) or not mood.strip():
        warnings.append("`mood` is recommended to help downstream curation.")

    if not isinstance(tags, list) or not tags:
        warnings.append("`tags` array is recommended for filtering (minimum 2).")
    else:
        if len(tags) < 2:
            warnings.append("Provide at least 2 tags for better discovery.")
        for index, tag in enumerate(tags, start=1):
            if not isinstance(tag, str) or not tag.strip():
                errors.append(f"Tag #{index} must be a non-empty string.")
            elif tag != tag.lower():
                warnings.append(f"Tag \"{tag}\" should be lowercase.")

    if not isinstance(summary, str) or not summary.strip():
        warnings.append("`summary` is recommended to describe the arrangement.")

    resources = metadata.get("resources")
    if resources is not None:
        if not isinstance(resources, list):
            errors.append("`resources` must be a list of strings if provided.")
        else:
            for index, resource in enumerate(resources, start=1):
                if not isinstance(resource, str) or not resource.strip():
                    warnings.append(f"Resource #{index} should be a non-empty string.")

    return errors, warnings


def validate_pattern_code(code: str | None) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if code is None or not isinstance(code, str) or not code.strip():
        errors.append("Pattern body is empty.")
        return errors, warnings

    stripped = code.replace(" ", "")
    if "setcpm(" not in stripped and "setcps(" not in stripped:
        warnings.append("Set tempo explicitly with `setcpm(...)` once near the top.")

    for match in GAIN_PATTERN.finditer(code):
        try:
            numeric = float(match.group(1))
        except ValueError:
            continue
        if numeric > 1:
            warnings.append(
                f"Gain literal {numeric} detected; consider keeping it <= 1 to avoid clipping."
            )

    return errors, warnings


__all__ = ["validate_metadata", "validate_pattern_code", "SLUG_PATTERN"]
