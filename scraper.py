import datetime
import glob
import re
import shutil
from urllib.parse import quote
import json

import lxml.html
import scraperwiki


def process_one(entry, url):
    source_list = entry.xpath("./text()")
    if len(source_list) > 0:
        source = source_list[0]
    else:
        source = ""

    head = entry.xpath("./following-sibling::h1[1]/text()")[0]

    # add all parts to one large string
    raw_text = ""
    for part in entry.xpath("./following-sibling::div[1]/p/text()"):
        raw_text += " " + part
    text = re.sub(r"<!--.*-->", "", raw_text).strip()

    head_split = head.split()

    raw_date = head_split[0]
    date = datetime.datetime.strptime(raw_date, "%d.%m.%Y").isoformat()

    # just location
    raw_location = " ".join(head_split[1 : len(head_split)])

    county = re.match('"\(.*|\/.*"', raw_location)
    if not county is None:
        county = county.group(1)
        county = county.replace("(", "").replace(")", "")
    # TODO: What is about landkreise?
    # but sometimes with 'Landkreisen'
    # we want to clean the data and remove them
    location = fix_location.sub("", raw_location)

    # sometimes new white spaces need to be stripped again
    location = location.strip()

    source_name = source
    source_date = ""
    if "," in source:
        sep_source = source.rindex(",")
        try:
            source_date = datetime.datetime.strptime(
                source[sep_source + 1 :], "%d.%m.%Y"
            ).isoformat()
            source_name = source[:sep_source]
        except:
            pass

    uri = url + "#" + quote(date + "-" + location)

    scraperwiki.sqlite.save(
        unique_keys=["uri"],
        data={
            "sources": json.dumps({"name": source_name, "date": source_date}),
            "description": text,
            "startDate": date,
            "locations": json.dumps([location, "Sachsen-Anhalt", "Germany"]),
            "iso3166_2": "DE-ST",
            "uri": uri,
        },
        table_name="data",  # broken right now
    )


base_url = "http://www.mobile-opferberatung.de/monitoring/chronik%s/"

fix_location = re.compile("\(.*|\/.*")
indices = range(2003, datetime.datetime.now().year + 1)

for i in indices:

    url = base_url % i

    # special case for 2019
    if i == 2019:
        url = url.replace("chronik2019", "chronik-2019")

    print("Sending Requests:")
    print(url)

    html = scraperwiki.scrape(url)
    doc = lxml.html.fromstring(html)

    for entry in doc.xpath("//h5"):
        process_one(entry, url)

# This is a hotfix. Right now, the custom naming of the table is broken.
shutil.move(glob.glob("./*.sqlite")[0], "data.sqlite")
