"""Transparent, rule-based competition assessment (no LLM)."""

NEARBY_THRESHOLD_M = 250


def assess_competition(count_within_radius: int, closest_distance_m: float | None, category: str, radius_m: int) -> str:
    """Produce a short, evidence-based competition statement.

    Rules (per assignment spec):
      0-1 matches  -> Lower observed direct competition
      2-4 matches  -> Moderate observed direct competition
      5+ matches   -> Higher observed direct competition
      closest < 250m -> add a note that a direct competitor is very nearby
    """
    if count_within_radius <= 1:
        level = "Lower"
    elif count_within_radius <= 4:
        level = "Moderate"
    else:
        level = "Higher"

    radius_km = radius_m / 1000
    plural = "es" if category == "cafe" else "s"
    category_plural = f"{category}{plural}"

    if count_within_radius == 0:
        summary = (
            f"Indicative competition assessment: {level.lower()}. "
            f"The OpenStreetMap query found no mapped {category_plural} within {radius_km:g} km "
            f"of the proposed location."
        )
    else:
        summary = (
            f"Indicative competition assessment: {level.lower()}. "
            f"The OpenStreetMap query identified {count_within_radius} mapped {category_plural} "
            f"within {radius_km:g} km of the proposed location. "
            f"The nearest mapped {category} is approximately {closest_distance_m:.0f} metres away."
        )

    if closest_distance_m is not None and closest_distance_m < NEARBY_THRESHOLD_M:
        summary += (
            f" Note: a direct competitor is very nearby (under {NEARBY_THRESHOLD_M} m)."
        )

    summary += (
        " Validate these results through local field research and a clearer definition "
        "of the intended concept before making a location decision."
    )
    return summary


LIMITATIONS_STATEMENT = (
    "OpenStreetMap is a crowd-sourced dataset. Venue metadata (names, categories, websites) "
    "may be incomplete, outdated, or missing entirely, and newly opened or closed businesses "
    "may not yet be reflected. Treat these results as an indication, not a complete market "
    "survey, and validate findings through local field research before making a real business "
    "decision."
)
