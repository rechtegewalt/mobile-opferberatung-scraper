import datetime
import glob
import re
import sys
import os
from urllib.parse import quote

import lxml.html

os.environ["SCRAPERWIKI_DATABASE_NAME"] = "sqlite:///data.sqlite"

import scraperwiki

# simple enviroment
debug = len(sys.argv) > 1

# 11.02.2005
def extract_data_format_1(source, sep_source):
    source_date_string = source[sep_source + 1 :].strip()
    source_date = datetime.datetime.strptime(source_date_string, "%d.%m.%Y")
    source_name = source[:sep_source]
    return source_name, source_date


# 11.02.05
def extract_data_format_2(source, sep_source):
    source_date_string = source[sep_source + 1 :].strip()
    source_date = datetime.datetime.strptime(source_date_string, "%d.%m.%y")
    source_name = source[:sep_source]
    return source_name, source_date


def extract_sources(source_list):
    # sometimes they concat sources with ; so try to get them
    source_list_fixed = []
    for s in source_list:
        source_list_fixed += s.split(";")
    source_list = source_list_fixed

    sources = []
    for source in source_list:
        source_name = source
        source_date = None 
        if "," in source:
            sep_source = source.rindex(",")
            done = False
            # parse
            try:
                source_name, source_date = extract_data_format_1(source, sep_source)
                done = True
            except BaseException as e:
                if debug:
                    print(source)
                    print(str(e))
            if not done:
                try:
                    source_name, source_date = extract_data_format_2(source, sep_source)
                except BaseException as e:
                    if debug:
                        print(source)
                        print(str(e))
        sources.append({"name": source_name, "date": source_date})

    return sources


def extract_location(location):
    # print(raw_location)
    county = re.findall(r"\(.*\)", location)
    if len(county) > 0:
        county = county[0]
        county = county.replace("(", "").replace(")", "")

        # special case for Halle Saale
        if county == "Saale":
            county = []
        else:
            # remove landkreis from location
            location = re.sub(r"\(.*|\/.*", "", location)

    # sometimes new white spaces need to be stripped again
    location = location.strip()
    if len(county) == 0:
        location_final = ", ".join([location, "Sachsen-Anhalt", "Deutschland"])
    else:
        location_final = ", ".join([location, county, "Sachsen-Anhalt", "Deutschland"])
    return location_final


def process_one(entry, url):
    source_list = entry.xpath("./text()")
    sources = extract_sources(source_list)

    head = entry.xpath("./following-sibling::h1[1]/text()")[0]

    # add all parts to one large string
    raw_text = ""
    for part in entry.xpath("./following-sibling::div[1]/p/text()"):
        raw_text += " " + part
    text = re.sub(r"<!--.*-->", "", raw_text).strip()

    head_split = head.split()
    raw_date = head_split[0]
    date = datetime.datetime.strptime(raw_date, "%d.%m.%Y")
    # just location
    raw_location = " ".join(head_split[1:])
    location = extract_location(raw_location)
    uri = url + "#" + quote(date.isoformat() + "-" + location)

    scraperwiki.sqlite.save(
        unique_keys=["uri"],
        data={"description": text, "startDate": date, "iso3166_2": "DE-ST", "uri": uri},
        table_name="data",
    )

    scraperwiki.sqlite.save(
        unique_keys=["reportURI"],
        data={"subdivisions": location, "reportURI": uri},
        table_name="location",
    )

    for s in sources:
        scraperwiki.sqlite.save(
            unique_keys=["reportURI"],
            data={"publishedDate": s["date"], "name": s["name"], "reportURI": uri},
            table_name="source",
        )


base_url = "http://www.mobile-opferberatung.de/monitoring/chronik%s/"

indices = range(2003, datetime.datetime.now().year + 1)

for i in indices:

    url = base_url % i

    # special case for 2019
    if i == 2019:
        url = url.replace("chronik2019", "chronik-2019")

    print("Sending Requests:")
    print(url)

    try:
        html = scraperwiki.scrape(url)
    except Exception as e:
        print('some error,', e)

    doc = lxml.html.fromstring(html)

    for entry in doc.xpath("//h5"):
        process_one(entry, url)
