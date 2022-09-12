# Scrapes Rules of Origin data

## Implementation steps

### Create and activate a virtual environment, e.g.

- `python3 -m venv venv/`
- `source venv/bin/activate`
- Install necessary Python modules via `pip3 install -r requirements.txt`

### Environment variable settings

#### Database
- DATABASE_UK=postgres connection string
- SAVE_TO_DB=[0|1]
- OVERWRITE_DB=[0|1]

#### Templates for accessing the raw data
- url_template=path to JSON for template - modern
- url_template_classic=path to JSON for template - legacy / classic

#### Paths
- commodity_code_folder=folder for commodity codes
- EXPORT_PATH=string
- EXPORT_PATH_UK=string
- EXPORT_PATH_XI=string

#### Configuration
- CHAPTERS_TO_PROCESS=""
- INSERT_HYPERLINKS=[0|1]
- MIN_CODE=Replace this with a valid 10-digit commodity code to restart processing from a specific code
- MAX_CODE=Replace this with a valid 10-digit commodity code to stop processing at a specific code
- SPECIFIC_COUNTRY=Overrides the country list to pull data from a specific country only
- SPECIFIC_CODE="Overrides the commodity list to pull data for a single commodity only

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

### What process_roo.py does

#### For Classic Rules of origin (e.g. GSP)

This is all a lot harder than the work on Word documents, as it does not allow you to change the originals

1. Having downloaded all of the JSONs for each chapter in a previous step ...
2. Create a new ClassicRoo object against each
3. Main cleansing rules are stored in classic_roo > **cleanse_rules**
4. Main code to form relevant data are stored in classic_roo > **deconstruct_rules_html**
5. deconstruct_rules_html creates a **ClassicRooRow** object for every table row in the MADB html
6. ClassicRooRow is where the actual formation of destination data is completed
   1. It creates a series of ClassicRooCell objects under the self.cells object