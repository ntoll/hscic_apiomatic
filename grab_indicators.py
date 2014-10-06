# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Grabs all the indicators published by HSCIC.

Each indicator has a unique ID. Currently (October 2014) the upper limit is
1698. Each indicator can be obtained with the following URL (remembering to
replace the integer value at the end):


https://indicators.ic.nhs.uk/webview/velocity?v=2&mode=documentation&submode=ddi&study=http%3A%2F%2F172.16.9.26%3A80%2Fobj%2FfStudy%2FP01698
"""
import os
import json
import logging
import requests
from bs4 import BeautifulSoup


logging.basicConfig(filename='indicators.log',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.DEBUG)


URL_TEMPLATE = "https://indicators.ic.nhs.uk/webview/velocity?v=2&mode=documentation&submode=ddi&study=http%3A%2F%2F172.16.9.26%3A80%2Fobj%2FfStudy%2FP{:05}"


def get_indicator(i, directory):
    """
    Checks if a cached copy of the HTML for the referenced indicator exists in
    the referenced directory. If not will attempt to fetch and cache it.

    Will then return a dict containing metadata extracted from the HTML.
    """
    logging.info(i)
    path = os.path.join(directory, '{}.html'.format(i))
    html = ''
    if os.path.isfile(path):
        html = open(path).read()
    else:
        url = URL_TEMPLATE.format(i)
        logging.info('Requesting {}'.format(url))
        response = requests.get(url)
        logging.info(response.status_code)
        if response.status_code < 400:
            html = response.text
            with open(path, 'wb') as cached:
                cached.write(html)
    result = {}
    if html:
        soup = BeautifulSoup(html)
        data = soup.find(id="metadata")
        children = []
        for child in data.children:
            if hasattr(child, 'text'):
                clean = child.text.strip()
            else:
                clean = child.string.strip()
            if clean:
                children.append(clean)
        if children:
            for x in range(0, len(children), 2):
                if hasattr(children[x], 'text'):
                    key = children[x].text.strip().lower()
                else:
                    key = children[x].strip().lower()
                if hasattr(children[x+1], 'text'):
                    value = children[x+1].text.strip()
                else:
                    value = children[x+1].strip()
                if key == 'keyword(s)':
                    value = [tag for tag in value.split('\r\n')
                             if tag.strip()]
                if key == 'download(s)':
                    break
                result[key] = value
            links = data.find_all('a')
            sources = []
            for source in links:
                url = 'https://indicators.ic.nhs.uk' + source.attrs['href']
                description = source.text
                filetype = url[url.rfind('.') + 1:]
                sources.append({
                    'url': url,
                    'description': description.replace('.{}'.format(filetype),
                                                       ''),
                    'filetype': filetype,
                })
            result['sources'] = sources
    return result


if __name__ == '__main__':
    result = []
    directory = 'indicators_raw'
    filename = 'indicators.json'
    if not os.path.exists(directory):
        logging.info('Creating directory {}'.format(directory))
        os.makedirs(directory)
    for i in range(1, 1699):
        try:
            indicator = get_indicator(i, directory)
            if indicator:
                result.append(indicator)
        except Exception as ex:
            logging.error(ex)
    json.dump(result, open(filename, 'wb'), indent=2)
    logging.info('Written results to {}'.format(filename))
