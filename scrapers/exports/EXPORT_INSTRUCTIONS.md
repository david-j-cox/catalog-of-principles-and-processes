# How to Export Abstracts for the Catalog

We need abstracts for ~676 JEP:ALC articles (PsycNET) and ~638 BP articles (ScienceDirect).

After exporting, drop the CSV files in this folder and run:
```
python scrapers/merge_exported_abstracts.py scrapers/exports/*.csv
```

---

## PsycNET — JEP:ALC (676 articles, mostly 1975–2004)

PsycNET limits exports to 2,000 records at a time, so one search should cover everything.

### Steps:

1. Go to **https://psycnet.apa.org/** and log in via your Endicott library
2. Click **Advanced Search**
3. Set these filters:
   - **Publication Title**: `Journal of Experimental Psychology: Animal Behavior Processes` OR `Journal of Experimental Psychology: Animal Learning and Cognition`
   - **Year**: `1975` to `2004`  (covers the bulk of the gaps)
4. Run the search
5. Select all results (checkbox at top)
6. Click **Export** → choose **CSV**
7. Make sure **Abstract** is checked in the fields list
8. Download and save as `scrapers/exports/psycnet_1975_2004.csv`

Then repeat for the remaining years with gaps:
   - **Year**: `2005` to `2026`
   - Save as `scrapers/exports/psycnet_2005_2026.csv`

### What the CSV should look like:
```
"Title","Authors","Year","DOI","Abstract",...
"Some Article","Smith, J.","1982","10.1037/0097-7403.8.1.1","The abstract text..."
```

---

## ScienceDirect — BP (638 articles, mostly 1976–2009)

ScienceDirect's export is more limited — max 100 at a time. You'll need to do
multiple exports by year range.

### Steps:

1. Go to **https://www.sciencedirect.com/search**
2. Search with these filters:
   - **Journal**: `Behavioural Processes`
   - **Year range**: `1976` to `1985` (start with the biggest gap)
3. Select all results on the page (checkbox at top)
4. Click **Export** → **CSV** → make sure **Abstract** is included
5. If there are multiple pages, repeat select-all + export for each page
6. Save as `scrapers/exports/bp_1976_1985.csv`

Repeat for these year ranges (covering the main gaps):
- 1986–1995
- 1996–2005
- 2006–2015
- 2016–2026

### Alternative: ScienceDirect search by no-abstract filter

You can also try searching by specific DOIs. But the year-range approach
is likely faster since most articles in these ranges are missing abstracts.

---

## After Exporting

```bash
# Preview what will be merged (no changes)
python scrapers/merge_exported_abstracts.py --dry-run scrapers/exports/*.csv

# Merge into data.json
python scrapers/merge_exported_abstracts.py scrapers/exports/*.csv
```

The merge script:
- Matches by DOI (case-insensitive)
- Never overwrites existing abstracts
- Handles both CSV and RIS formats
- Strips HTML tags from abstracts
