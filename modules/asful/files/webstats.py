#!/usr/bin/env python
from elasticsearch import Elasticsearch, helpers
from pyexcel_ods import save_data
from collections import *

es = Elasticsearch([
                    {'host': 'localhost', 'port': 9200, 'url_prefix': '', 'use_ssl': False},
                ])
        

def makeBook(domain):
        book = OrderedDict()
        
        # JS shortcut stuff, bleh
        false = False
        true = True
        
        
        # Get unique IPs
        
        query = {"query":{"bool":{"must":[{"query_string":{"query":"vhost:\"%s\" AND document:*.html AND useragent:mozilla" % domain,"analyze_wildcard":True}},{"range":{"@timestamp":{"gte":"now-30d","lte":"now","format":"epoch_millis"}}}],"must_not":[]}},"size":0,"_source":{"excludes":[]},"aggs":{"uniques":{"date_histogram":{"field":"@timestamp","interval":"1d","time_zone":"Europe/Berlin","min_doc_count":1},"aggs":{"1":{"cardinality":{"field":"clientip.keyword"}}}}}}        
        res = es.search(index='loggy-*', request_timeout=90, body = query)
        
        y = 0
        arr = [['Date', 'Unique visitors']]
        for el in res['aggregations']['uniques']['buckets']:
                d = el['key_as_string'].replace(' 00:00:00', '')
                c = el['1']['value']
                y += 1
                arr.append([d,c])
        book.update({'Unique visitors, past month': arr})
        
        
        
        # Get page views
        
        
        query = {"query":{"bool":{"must":[{"query_string":{"query":"vhost:\"%s\" AND document:*.html AND useragent:mozilla" % domain,"analyze_wildcard":True}},{"range":{"@timestamp":{"gte":"now-30d","lte":"now","format":"epoch_millis"}}}],"must_not":[]}},"size":0,"_source":{"excludes":[]},"aggs":{"uniques":{"date_histogram":{"field":"@timestamp","interval":"1d","time_zone":"Europe/Berlin","min_doc_count":1}}}}        
        res = es.search(index='loggy-*', request_timeout=90, body = query)
        
        y = 0
        arr = [['Date', 'Pageviews']]
        for el in res['aggregations']['uniques']['buckets']:
                d = el['key_as_string'].replace(' 00:00:00', '')
                c = el['doc_count']
                y += 1
                arr.append([d,c])
        book.update({'Pageviews, past month': arr})
        
        
        
        # Get most visited pages
        arr = [['URI', 'Pageviews']]
        
        query = {"query":{"bool":{"must":[{"query_string":{"query":"vhost:\"%s\" AND uri:*.html AND useragent:mozilla" % domain,"analyze_wildcard":true}},{"range":{"@timestamp":{"gte":"now-30d","lte":"now","format":"epoch_millis"}}}],"must_not":[]}},"size":0,"_source":{"excludes":[]},"aggs":{"2":{"terms":{"field":"uri.keyword","size":50,"order":{"_count":"desc"}}}}}
        res = es.search(index='loggy-*', request_timeout=90, body = query)
        
        y = 0
        for el in res['aggregations']['2']['buckets']:
                d = el['key'].replace(' 00:00:00', '')
                c = el['doc_count']
                y += 1
                arr.append([d,c])
        book.update({'Most visited pages, past month': arr})
        
        
        
        # Geomapping
        
        query = {"query":{"bool":{"must":[{"query_string":{"query":"vhost:\"%s\" AND useragent:mozilla AND NOT (geo_country.keyword in (\"EU\", \"AP\", \"A1\", \"A2\", \"SX\", \"SS\", \"-\")) AND NOT geo_country.keyword:\"-\"" % domain,"analyze_wildcard":true}},{"range":{"@timestamp":{"gte":"now-30d","lte":"now","format":"epoch_millis"}}}],"must_not":[]}},"size":0,"_source":{"excludes":[]},"aggs":{"2":{"terms":{"field":"geo_country.keyword","size":200,"order":{"_count":"desc"}}}}}
        res = es.search(index='loggy-*', request_timeout=90, body = query)
        
        arr = [['Country', 'Pageviews']]
        
        y = 0
        for el in res['aggregations']['2']['buckets']:
                d = el['key']
                c = el['doc_count']
                y += 1
                arr.append([d,c])
        book.update({'Geomapping, past month': arr})
        
        
        save_data("/var/www/snappy/exports/%s.ods" % domain, book)

domains = open("/var/www/snappy/domains.txt").read().split()
for sdomain in domains:
        if sdomain:
                makeBook(sdomain)
