# HORECA Competition Lens

A small local Flask app for the HHS AI Taskforce preparation assignment. It lets an
aspiring café/restaurant/hotel owner enter an address, see the closest mapped
OpenStreetMap competitors within 1 km, and generate a Quarto PDF report with a
transparent, rule-based competition assessment.

## Stack

- Python + Flask
- OpenStreetMap: Nominatim (geocoding) + Overpass (venue search)
- Quarto (rendered to PDF)

## Setup

1. Create and activate a virtual environment, then install dependencies:

   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Install [Quarto](https://quarto.org/docs/get-started/) and TinyTeX (needed once, for PDF rendering):

   ```
   quarto install tinytex
   ```

3. Run the app:

   ```
   python app.py
   ```

4. Open http://127.0.0.1:5000, enter an address, pick a category, and search.
   From the results page you can generate a PDF report.

## Notes

- Only public OpenStreetMap data is used. No API keys or secrets are required.
- Geocoding and venue-search results are cached in-memory per run to avoid
  sending repeated identical requests to Nominatim/Overpass while testing.
- The competition assessment is rule-based (no LLM) and lives in
  `services/assessment.py`.

## Reflection

**What worked well?**
The core pipeline — geocode an address, query Overpass for nearby venues, compute
distances, and render a rule-based assessment — worked correctly on the first
implementation pass. Both edge cases (many competitors and zero competitors) produced
sensible output without extra fixes.

**What did not work at first?**
Generating the Quarto PDF failed twice before it worked:
1. Quarto defaulted to a different, globally-installed Python interpreter that didn't
   have the project's dependencies (pandas, jupyter), causing a `ModuleNotFoundError`.
2. Once that was fixed, Quarto still couldn't find a TeX engine to produce the PDF —
   TinyTeX wasn't installed yet.
3. Separately, a Flask session's PATH didn't pick up the newly-installed `quarto`
   command, so the app itself couldn't find the executable even though it worked from
   a fresh terminal.

**What is one issue you solved by iterating with your coding harness?**
The Python-mismatch issue above: the fix was to explicitly set the `QUARTO_PYTHON`
environment variable to the project's own interpreter (`sys.executable`) whenever the
Flask app invokes `quarto render`, instead of relying on whatever Python happens to be
first on the system PATH. I also found that failures were silently invisible in the UI
because the results template never actually rendered the `error` value it was being
passed — fixed by adding the missing block to the template.

**What is one thing you still do not understand or want to discuss during the workshop?**
One search (a central address in The Hague) returned around 300 matching restaurants
within a 1 km radius, which seems high. I'd like to discuss whether that's plausible for
a dense OSM-mapped city center, or whether it points to a query issue (e.g. Overpass
`around` matching more loosely than expected, or double-counting nodes vs. ways for the
same venue).
