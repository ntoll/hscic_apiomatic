hscic_apiomatic
===============

Scrapes HSCIC website and builds a list of JSON objects for each dataset found
therein.

Requires beautifulsoup and requests::

    $ pip install -r requirements.txt

Usage
-----

To generate an output file called hscic.json::

    $ python scrape.py
