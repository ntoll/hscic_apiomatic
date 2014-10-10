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

If anything goes wrong check out the indicator.log / datasets.log files. :-)

Feedback most welcome!

@ntoll
