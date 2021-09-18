# Scrapes Rules of Origin data

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python3 -m venv venv/`
  `source venv/bin/activate`

- Environment variable settings

  - DATABASE_UK=postgres connection string
  - MIN_CODE="0" -- Replace this with a valid 10-digit commodity code to restart processing from a specific code
  - SPECIFIC_COUNTRY="ME" -- Overrides the country list to pull data from a specific country only
  - SPECIFIC_CODE="1514111000" -- Overrides the commodity list to pull data for a single commodity only
  - SAVE_TO_DB=1 -- Flag to save to the database or not
  - OVERWRITE_DB=1 -- Flag to determine if pre-existing data is to be overwritten

- Install necessary Python modules via `pip3 install -r requirements.txt`

## Usage

### The countries.json configuration file

- This file contains a list of all of the countries for which we are scraping data
- Each country item is structured as follows:

  `{
      "code": "AF",
      "prefix": "gsp",
      "omit": 0,
      "source": "classic"
  }`

  where:

  - code is the 2-digit ISO country code to that is used as an input into the scrape function
  - prefix is the code against which the data is registered in the local database
  - omit (0 | 1) which determines if the country is to be 'skipped' or not
  - source indicates the following, dependent on the value:
    - if 'classic', then the RoO are structured using the old fashioned Trade Helpdesk structures
    - if 'product', then using the new MADB / ROSA product-specific rules (PSR)
  - At the time of writing, GSP, Turkey and Kenya used the old style
      

### To scrape source:

  `python3 scrape_roo.py`

- This will download the RoO from the source
- Saves as complete JSON documents locally
- Use process_roo to process them: no processing done in this step (just downloading)

### To process the JSONs:

  `python3 process_roo.py`

- This takes the downloaded RoO JSON source files and converts them into the necessary data objects + stores in local Postgres database

### To export to new JSON:

  `python3 export_to_json.py`

- This runs through the Postgres database and creates a JSON file that can be used in the OTT prototype