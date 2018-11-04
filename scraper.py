import datetime
import glob
import re
import shutil

import lxml.html
import scraperwiki


def process_one(entry):
    source_list = entry.xpath("./text()")
    if len(source_list) > 0:
        source = source_list[0]
    else:
        source = "Unbekannt"

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

    # TODO: What is about landkreise?
    # but sometimes with 'Landkreisen'
    # we want to clean the data and remove them
    location = fix_location.sub("", raw_location)

    # sometimes new white spaces need to be stripped again
    location = location.strip()

    scraperwiki.sqlite.save(
        unique_keys=["source", "text", "date", "location"],
        data={"source": source, "text": text, "date": date, "location": location},
        table_name="data" # broken right now
    )


base_url = "http://www.mobile-opferberatung.de/monitoring/chronik%s/"

fix_location = re.compile("\(.*|\/.*")
indices = range(2003, datetime.datetime.now().year + 1)

for i in indices:

    url = base_url % i

    print("Sending Requests:")
    print(url)

    html = scraperwiki.scrape(url)
    doc = lxml.html.fromstring(html)

    for entry in doc.xpath("//h5"):
        process_one(entry)

# This is a hotfix. Right now, the custom naming of the table is broken.
shutil.move(glob.glob('./*.sqlite')[0], "data.sqlite")
