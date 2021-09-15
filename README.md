# Scrapes Rules of Origin data

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python3 -m venv venv/`
  `source venv/bin/activate`

- Environment variable settings

  - DATABASE_UK=postgres connection string
  - MIN_CODE="0"
  - xSPECIFIC_COUNTRY="ME"
  - xSPECIFIC_CODE="1514111000"
  - SAVE_TO_DB=1
  - OVERWRITE_DB=1

- Install necessary Python modules via `pip3 install -r requirements.txt`

## Usage

### To scrape source:
- This will download the RoO from the source
- Saves as complete JSON documents locally
- Use process_roo to process them: no processing done in this step (just downloading)

  `python3 scrape_roo.py`

### To process the JSONs:
`python3 process_roo.py`

### To export to new JSON:
`python3 export_to_json.py`
