"""HORECA Competition Lens — local Flask app.

Lets a user enter an address, pick a venue category (cafe/restaurant/hotel),
and see the closest matching OpenStreetMap-mapped competitors within 1 km,
plus generate a Quarto PDF report of the analysis.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from services.assessment import LIMITATIONS_STATEMENT, assess_competition
from services.osm import (
    RADIUS_METERS,
    OsmLookupError,
    find_nearby_venues,
    geocode_address,
    suggest_addresses,
)

app = Flask(__name__)

REPORT_DIR = Path(__file__).parent / "report"
REPORT_DATA_PATH = REPORT_DIR / "report_data.json"
REPORT_QMD_PATH = REPORT_DIR / "report.qmd"
REPORT_OUTPUT_DIR = REPORT_DIR / "output"

VALID_CATEGORIES = {"cafe", "restaurant", "hotel"}

# Fallback for Windows sessions whose PATH hasn't been refreshed since Quarto
# was installed (e.g. a shell opened before the installer ran).
_WINDOWS_QUARTO_FALLBACK = Path("C:/Program Files/Quarto/bin/quarto.exe")


def find_quarto() -> str | None:
    on_path = shutil.which("quarto")
    if on_path:
        return on_path
    if _WINDOWS_QUARTO_FALLBACK.exists():
        return str(_WINDOWS_QUARTO_FALLBACK)
    return None


def run_search(address: str, category: str) -> dict:
    """Geocode the address, query Overpass, and build the result payload."""
    lat, lon = geocode_address(address)
    venues = find_nearby_venues(lat, lon, category)
    top5 = venues[:5]
    closest_distance = venues[0]["distance_m"] if venues else None

    assessment_text = assess_competition(
        count_within_radius=len(venues),
        closest_distance_m=closest_distance,
        category=category,
        radius_m=RADIUS_METERS,
    )

    return {
        "address": address,
        "category": category,
        "radius_m": RADIUS_METERS,
        "venues": top5,
        "total_count": len(venues),
        "closest_distance_m": closest_distance,
        "assessment_text": assessment_text,
        "limitations": LIMITATIONS_STATEMENT,
    }


@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("q", "").strip()
    if len(query) < 3:
        return jsonify([])
    try:
        return jsonify(suggest_addresses(query))
    except Exception:
        return jsonify([])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    address = request.form.get("address", "").strip()
    category = request.form.get("category", "")

    if not address or category not in VALID_CATEGORIES:
        return render_template("index.html", error="Please enter an address and choose a valid category.", address=address, category=category)

    try:
        result = run_search(address, category)
    except OsmLookupError as exc:
        return render_template("index.html", error=str(exc), address=address, category=category)
    except Exception:
        return render_template("index.html", error="Something went wrong while searching OpenStreetMap. Please try again.", address=address, category=category)

    return render_template("results.html", **result)


@app.route("/report", methods=["POST"])
def report():
    address = request.form.get("address", "").strip()
    category = request.form.get("category", "")

    if not address or category not in VALID_CATEGORIES:
        return render_template("index.html", error="Please enter an address and choose a valid category.")

    try:
        result = run_search(address, category)
    except OsmLookupError as exc:
        return render_template("index.html", error=str(exc), address=address, category=category)
    except Exception:
        return render_template(
            "index.html",
            error="Something went wrong while searching OpenStreetMap (it may be temporarily unavailable). Please try again.",
            address=address, category=category,
        )

    REPORT_DATA_PATH.write_text(json.dumps(result, indent=2))
    REPORT_OUTPUT_DIR.mkdir(exist_ok=True)

    quarto_exe = find_quarto()
    if not quarto_exe:
        return render_template(
            "results.html", **result,
            error="Quarto is not installed or not on PATH. Install Quarto to generate the PDF report.",
        )

    try:
        env = os.environ.copy()
        env["QUARTO_PYTHON"] = sys.executable
        subprocess.run(
            [quarto_exe, "render", str(REPORT_QMD_PATH), "--to", "pdf", "--output-dir", str(REPORT_OUTPUT_DIR)],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPORT_DIR,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        return render_template(
            "results.html", **result,
            error=f"Quarto render failed: {exc.stderr[-800:] if exc.stderr else exc}",
        )

    pdf_path = REPORT_OUTPUT_DIR / "report.pdf"
    return send_file(pdf_path, as_attachment=True, download_name="horeca_competition_report.pdf")


if __name__ == "__main__":
    app.run(debug=True)
