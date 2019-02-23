# Mobile Opferberatung Scraper

Scraping right-wing incidents in Sachsen-Anhalt, Germany as monitored by the NGO [Mobile Opferberatung](https://www.mobile-opferberatung.de/).

-   Website: http://www.mobile-opferberatung.de/monitoring/chronik2018/
-   Data: https://morph.io/jfilter/mobile-opferberatung-scraper

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

## License

MIT.
