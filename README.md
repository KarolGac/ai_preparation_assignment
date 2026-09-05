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
The main flow (address to Overpass search to distances to rule-based assessment) worked
on the first try. Both edge cases I tested (lots of competitors, zero competitors) gave
sensible results without needing fixes.

**What did not work at first?**
Generating the PDF failed a few times before it worked:
1. Quarto ran the wrong Python (not the project's), so it was missing pandas/jupyter.
2. Quarto also couldn't find a TeX engine yet, since TinyTeX wasn't installed.
3. Even after installing Quarto, my terminal session didn't see it on PATH right away.

**What is one issue you solved by iterating with your coding harness?**
Fixed the Python mismatch by explicitly pointing Quarto to the project's own Python
whenever it renders the report, instead of whatever Python happened to be found first.
I also noticed error messages weren't showing up in the UI at all, the template was
just missing the line that displays them, so I added it.

**What is one thing you still do not understand or want to discuss during the workshop?**
One search near central The Hague returned around 300 matching restaurants within 1 km.
That feels high, I'd like to discuss whether that's realistic for a dense city center or
a sign of something off in the Overpass query.
