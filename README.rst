hscic_apiomatic
===============

Scrapes HSCIC website and builds a list of JSON objects for each dataset or
key indicator found therein.

Requires beautifulsoup, requests and html2text::

    $ pip install -r requirements.txt

Usage
-----

To scrape the indicator portal::

    $ python grab_indicators.py

To scrape the current dataset catalogue::

    $ python grab_datasets.py

The results are two JSON files: indicators.json and datasets.json.

(The existing indicators.json and datasets.json files in the repos were
generated at the beginning of October 2014. These can probably be ignored but
are included for illustrative purposes.)

If anything goes wrong check out the indicator.log / datasets.log files. :-)

Feedback most welcome!

@ntoll
