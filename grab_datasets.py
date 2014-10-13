# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Generates a list of JSON objects, one object for each dataset retrieved from
the HSCIC website.
"""
import os
import string
import json
import logging
import requests
import urllib
import html2text
from bs4 import BeautifulSoup
from urlparse import urlparse


logging.basicConfig(filename='datasets.log',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.DEBUG)


def get_query_dict(query):
    """
    Given a query string will return a dict representation thereof.
    """
    result = {}
    items = query.split('&')
    for i in items:
        k, v = i.split('=')
        result[urllib.unquote(k)] = urllib.unquote(v)
    return result


def get_datasets(dom):
    """
    Given a BeautifulSoup DOM will return a list of all the dataset's ids
    found therein.
    """
    result = []
    datasets = dom.find_all('a', 'HSCICProducts')
    for dataset in datasets:
        url = urlparse(dataset.attrs['href'])
        query = get_query_dict(url.query)
        result.append(int(query['productid']))
    return result


def get_parsed_url(parsed, query):
    """
    Given a parsed URL and updated query dictionary, will return a string
    representation of the updated URL.
    """
    return '{}://{}{}?{}'.format(parsed.scheme, parsed.netloc, parsed.path,
                                  urllib.urlencode(query))


def get_datasets_from_paginated_results(start_url):
    """
    Given a start URL will attempt to paginate through the results and return
    a list of dataset ids that constitute the result.
    """
    result = []
    logging.info('Getting paginated results for {}'.format(start_url))
    parsed = urlparse(start_url)
    query = get_query_dict(parsed.query)
    query['size'] = '100'
    query['page'] = '1'
    # Grab the first page.
    url = get_parsed_url(parsed, query)
    logging.info('Requesting {}'.format(url))
    response = requests.get(url)
    logging.info(response.status_code)
    if response.status_code < 400:
        # Work out how many further pages there are.
        first_page_soup = BeautifulSoup(response.text)
        result.extend(get_datasets(first_page_soup))
        paging = first_page_soup.find(id='paging')
        last_page_anchor = paging.find('a', 'last')
        if last_page_anchor:
            last_page = int(last_page_anchor.text)
            logging.info('Number of pages is {}'.format(last_page))
            # Iterate and parse them.
            if last_page > 1:
                for i in range(2, last_page+1):
                    query['page'] = str(i)
                    url = get_parsed_url(parsed, query)
                    logging.info('Requesting {}'.format(url))
                    response = requests.get(url)
                    logging.info(response.status_code)
                    if response.status_code < 400:
                        soup = BeautifulSoup(response.text)
                        result.extend(get_datasets(soup))
    logging.info('Number of datasets found: {}'.format(len(result)))
    return result


def get_keywords(cache):
    """
    Will attempt to retrieve a list of keywords and associated product_ids (the
    unique dataset identifier).
    """
    url_template = 'http://www.hscic.gov.uk/searchcatalogue?kwd={}&size=10&page=1#top'
    keywords = {}
    if os.path.isfile(cache):
        logging.info('Using cached records from {}'.format(cache))
        keywords = json.load(open(cache))
    else:
        for letter in string.ascii_lowercase:
            url = url_template.format(letter)
            logging.info('Requesting {}'.format(url))
            response = requests.get(url)
            logging.info(response.status_code)
            if response.status_code < 400:
                html = response.text
                soup = BeautifulSoup(html)
                kw = soup.find("ol", "keyword")
                if kw:
                    kids = kw.find("ol", "children")
                    if kids:
                        spans = kids.find_all("span", "heading")
                        for item in spans:
                            keywords[item.text] = []
    for key in keywords:
        if not keywords[key]:
            url = url_template.format(urllib.quote(key))
            keywords[key] = get_datasets_from_paginated_results(url)
    json.dump(keywords, open(cache, 'wb'), indent=2)
    logging.info('Saved complete keywords to {}'.format(cache))
    return keywords


def get_topics(cache):
    """
    Will attempt to retrieve a list of topics and associated product_ids (the
    unique dataset identifiers).
    """
    url_template = 'http://www.hscic.gov.uk/searchcatalogue?topics=0%2f{}&size=100&page=1'
    topics = {}
    if os.path.isfile(cache):
        logging.info('Using cached records from {}'.format(cache))
        topics = json.load(open(cache))
    else:
        url = "http://www.hscic.gov.uk/searchcatalogue"
        logging.info('Requesting {}'.format(url))
        response = requests.get(url)
        logging.info(response.status_code)
        if response.status_code < 400:
            html = response.text
            soup = BeautifulSoup(html)
            tops = soup.find("ol", "topic")
            if tops:
                spans = tops.find_all("span", "heading")
                for item in spans:
                    topics[item.text] = []
    for topic in topics:
        if not topics[topic]:
            url = url_template.format(urllib.quote(topic))
            topics[topic] = get_datasets_from_paginated_results(url)
    json.dump(topics, open(cache, 'wb'), indent=2)
    logging.info('Saved complete topics to {}'.format(cache))
    return topics


def get_info_types(cache):
    """
    Will attempt to retrieve a list of information types and associated
    product_ids.
    """
    url_template = 'http://www.hscic.gov.uk/searchcatalogue?infotype=0%2f{}&size=100&page=1'
    info_types = {}
    if os.path.isfile(cache):
        logging.info('Using cached records from {}'.format(cache))
        info_types = json.load(open(cache))
    else:
        url = "http://www.hscic.gov.uk/searchcatalogue"
        logging.info('Requesting {}'.format(url))
        response = requests.get(url)
        logging.info(response.status_code)
        if response.status_code < 400:
            html = response.text
            soup = BeautifulSoup(html)
            ts = soup.find("ol", "informationtype")
            if ts:
                spans = ts.find_all("span", "heading")
                for item in spans:
                    info_types[item.text] = []
    for it in info_types:
        if not info_types[it]:
            url = url_template.format(urllib.quote(it))
            info_types[it] = get_datasets_from_paginated_results(url)
    json.dump(info_types, open(cache, 'wb'), indent=2)
    logging.info('Saved complete information types to {}'.format(cache))
    return info_types


def get_dataset(dataset_id, dataset, directory):
    """
    Given an id and existing dict object representing the current meta-data
    about the dataset will extract all the things from the dataset's page on
    HSCIC.
    """
    url_template = 'http://www.hscic.gov.uk/searchcatalogue?productid={}'
    cache = os.path.join(directory, '{}.html'.format(dataset_id))
    html = ''
    url = url_template.format(dataset_id)
    if os.path.isfile(cache):
        logging.info('Using cached records from {}'.format(cache))
        html = open(cache).read()
    else:
        logging.info('Requesting {}'.format(url))
        response = requests.get(url)
        logging.info(response.status_code)
        if response.status_code < 400:
            html = response.text
            with open(cache, 'wb') as output:
                output.write(html.encode('utf-8'))
    if html:
        soup = BeautifulSoup(html)
        title = soup.find(id='headingtext').text.strip()
        logging.info(title)
        dataset['source'] = url
        dataset['title'] = title
        dataset['id'] = dataset_id
        product = soup.find(id='productview')
        pub_date = product.find('div',
                                'pubdate').text
        dataset['publication_date'] = pub_date.replace('Publication date: ',
                                                       '')
        summary = product.find('div', 'summary')
        if summary:
            summary = html2text.html2text(summary.prettify())
            dataset['summary'] = summary
        key_facts = product.find('div', 'notevalue')
        if key_facts:
            key_facts = html2text.html2text(key_facts.prettify())
            dataset['key_facts'] = key_facts
        resources = product.find_all('div', 'resourcelink')
        files = []
        for res in resources:
            anchor = res.find('a')
            url = anchor.attrs['href']
            if url.startswith('./'):
                url = 'http://www.hscic.gov.uk' + url[1:]
            filetype = url[url.rfind('.') + 1:]
            description = anchor.text.replace(' [.{}]'.format(filetype), '')
            files.append({
                'url': url,
                'description': description.strip(),
                'filetype': filetype,
            })
        dataset['sources'] = files
        date_range = product.find('div', 'daterange')
        if date_range:
            date_range = date_range.text.replace('Date Range: ', '')
            dataset['date_range'] = date_range
        coverage = product.find_all('div', 'coverage')
        geo = [x.text for x in coverage]
        if geo:
            dataset['geographical_coverage'] = geo
        return dataset
    else:
        return None

if __name__ == '__main__':
    result = []
    directory = 'datasets_raw'
    filename = 'datasets.json'
    if not os.path.exists(directory):
        logging.info('Creating directory {}'.format(directory))
        os.makedirs(directory)
    keywords = get_keywords(os.path.join(directory, 'keywords.json'))
    topics = get_topics(os.path.join(directory, 'topics.json'))
    information_types = get_info_types(os.path.join(directory,
                                                    'info_types.json'))
    datasets = {}
    for k in keywords:
        for dataset in keywords[k]:
            if dataset in datasets:
                datasets[dataset]['keywords'].append(k)
            else:
                datasets[dataset] = {
                    'keywords': [k, ],
                }
    for t in topics:
        for dataset in topics[t]:
            if dataset in datasets:
                if 'topics' in datasets[dataset]:
                    datasets[dataset]['topics'].append(t)
                else:
                    datasets[dataset]['topics'] = [t, ]
            else:
                datasets[dataset] = {
                    'topics': [t, ],
                }
    for i in information_types:
        for dataset in information_types[i]:
            if dataset in datasets:
                if 'information_types' in datasets[dataset]:
                    datasets[dataset]['information_types'].append(i)
                else:
                    datasets[dataset]['information_types'] = [i, ]
            else:
                datasets[dataset] = {
                    'information_types': [i, ],
                }
    print('Processing {} datasets'.format(len(datasets)))
    for k, v in datasets.iteritems():
        data = get_dataset(k, v, directory)
        if data:
            result.append(data)
    json.dump(result, open(filename, 'wb'), indent=2)
    logging.info('Written results to {}'.format(filename))
