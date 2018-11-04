# Mobile Opferberatung Scraper

Scraping right-wing incidents in Sachsen-Anhalt, Germany off the [Website](http://www.mobile-opferberatung.de/monitoring/chronik2018/) of the NGO "Mobile Opferberatung".

## Usage

For local development:

-   Install [Pipenv](https://github.com/pypa/pipenv)
-   `pipenv install`
-   `pipenv run python scraper.py`

For Morph:

-   `pipenv lock --requirements > requirements.txt`
-   commit the `requirements.txt`
-   modify `runtime.txt`

## Morph

This is a scraper that runs on [Morph](https://morph.io). To get started [see the documentation](https://morph.io/documentation)
