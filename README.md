# Scrapes Rules of Origin data

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python3 -m venv venv/`
  `source venv/bin/activate`

- Environment variable settings

  - DATABASE_UK=postgres connection string

- Install necessary Python modules via `pip3 install -r requirements.txt`

## Usage

### To scrape MADB:
- sfs
  `python3 scrape_madb.py`

### To process the JSONs:
`python3 process_madb.py`

### To export to new JSON:
`python3 export_to_json.py`
