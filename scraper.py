import datetime
import os
import re
from hashlib import md5

import lxml.html

os.environ["SCRAPERWIKI_DATABASE_NAME"] = "sqlite:///data.sqlite"

import scraperwiki

DEBUG = False

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
                if DEBUG:
                    print(source)
                    print(str(e))
            if not done:
                try:
                    source_name, source_date = extract_data_format_2(source, sep_source)
                except BaseException as e:
                    if DEBUG:
                        print(source)
                        print(str(e))
        sources.append({"name": source_name, "date": source_date})

    return sources


def extract_location(location):
    # print(raw_location)
    county = re.findall(r"\(.*\)", location)
    if len(county) > 0:
        county = county[0]
        county = (
            county.replace("(", "")
            .replace(")", "")
            .replace("Landkreis", "")
            .replace("LK ", "")
            .strip()
        )

        # special case for Halle Saale
        if "Saale" in county and "Halle" in location:
            county = []
        else:
            # remove landkreis from location
            location = re.sub(r"\(.*|\/.*", "", location)

    # sometimes new white spaces need to be stripped again
    location = location.strip()
    if len(county) == 0:
        return location, None
    return location, county


def legacy_parse(entry):
    source_list = entry.xpath("./text()")
    sources = extract_sources(source_list)

    head = entry.xpath("./following-sibling::h1[1]/text()")[0]

    # add all parts to one large string
    raw_text = ""
    for part in entry.xpath("./following-sibling::div[1]/p/text()"):
        raw_text += " " + part
    return sources, head, raw_text


def process_one(entry, url, legacy=False):
    if legacy:
        sources, head, raw_text = legacy_parse(entry)
    else:
        source_list = entry.xpath(".//h5//text()")
        sources = extract_sources(source_list)
        head = entry.xpath(".//h1//text()")[0]

        raw_text = ""
        for part in entry.xpath(".//p/text()"):
            raw_text += " " + part
    text = re.sub(r"<!--.*-->", "", raw_text).strip()

    head_split = head.split()
    raw_date = head_split[0]
    date = datetime.datetime.strptime(raw_date, "%d.%m.%Y")
    # just location
    raw_location = " ".join(head_split[1:])
    city, county = extract_location(raw_location)

    identifier = 'mobile-opferberatung-' + md5((url + date.isoformat() + city + text).encode()).hexdigest()

    scraperwiki.sqlite.save(
        unique_keys=["rg_id"],
        data={
            "description": text,
            "date": date,
            "url": url,
            "rg_id": identifier,
            "city": city,
            "county": county,
            "chronicler_name": "Mobile Opferberatung",
        },
        table_name="incidents",
    )

    for s in sources:
        scraperwiki.sqlite.save(
            unique_keys=["rg_id"],
            data={"date": s["date"], "name": s["name"], "rg_id": identifier},
            table_name="sources",
        )

    # force commit to prevent duplicates
    # https://github.com/sensiblecodeio/scraperwiki-python/issues/107
    scraperwiki.sqlite.commit_transactions()


base_url = "http://www.mobile-opferberatung.de/monitoring/chronik%s/"

indices = range(2003, datetime.datetime.now().year + 1)

for i in indices:

    url = base_url % i

    # special case for 2019+
    if i >= 2019:
        url = url.replace(f"{i}", f"-{i}")

    print(url)

    try:
        html = scraperwiki.scrape(url)
    except Exception as e:
        print("some error,", e)

    doc = lxml.html.fromstring(html)

    # only new cases are in the new format
    if i >= 2017:
        for entry in doc.xpath('//div[@class="entry-content"]')[0].xpath(
            './/div[contains(@class, "et_pb_with_border")]'
        ):
            process_one(entry, url)
    else:
        for entry in doc.xpath("//h5"):
            process_one(entry, url, legacy=True)

# save meta data

scraperwiki.sqlite.save(
    unique_keys=["chronicler_name"],
    data={
        "iso3166_1": "DE",
        "iso3166_2": "DE-ST",
        "chronicler_name": "Mobile Opferberatung",
        "chronicler_description": "Die Mobile Opferberatung in Trägerschaft von Miteinander e.V. unterstützt seit 2001 professionell und parteilich Betroffene rechter, rassistischer, antiromaistischer, lgbtiq-feindlicher, sozialdarwinistischer und antisemitischer Gewalt, deren Freundinnen, Angehörige sowie Zeug*innen in Sachsen-Anhalt.",
        "chronicler_url": "https://www.mobile-opferberatung.de/",
        "chronicle_source": "https://www.mobile-opferberatung.de/monitoring/chronik-2020/",
    },
    table_name="chronicle",
)

scraperwiki.sqlite.commit_transactions()
