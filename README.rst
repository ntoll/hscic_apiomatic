hscic_apiomatic
===============

Scrapes HSCIC website and builds a list of JSON objects for each dataset or
key indicator found therein.

Requires beautifulsoup and requests::

    $ pip install -r requirements.txt

Usage
-----

To scrape the indicator portal::

    $ python grab_indicators.py
