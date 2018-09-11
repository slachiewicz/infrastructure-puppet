#!/usr/bin/env python
import elasticsearch
import pyexcel_ods
import collections


# Elastic handler
es = elasticsearch.Elasticsearch([
        {'host': 'localhost', 'port': 9200, 'url_prefix': '', 'use_ssl': False},
])
        

# Make a "book" (an ODS file)
def makeBook(domain):
        book = collections.OrderedDict()
        
        # Get unique IPs
        query = {"query":{"bool":{"must":[{"query_string":{"query":"vhost:\"%s\" AND document:*.html AND useragent:mozilla" % domain,"analyze_wildcard":True}},{"range":{"@timestamp":{"gte":"now-30d","lte":"now","format":"epoch_millis"}}}],"must_not":[]}},"size":0,"_source":{"excludes":[]},"aggs":{"uniques":{"date_histogram":{"field":"@timestamp","interval":"1d","time_zone":"Europe/Berlin","min_doc_count":1},"aggs":{"1":{"cardinality":{"field":"clientip.keyword"}}}}}}        
        res = es.search(index='loggy-*', request_timeout=90, body = query)
        
        arr = [['Date', 'Unique visitors']]
        for el in res['aggregations']['uniques']['buckets']:
                d = el['key_as_string'].replace(' 00:00:00', '')
                c = el['1']['value']
                arr.append([d,c])
        book.update({'Unique visitors, past month': arr})
        
        
        
        # Get page views
        query = {"query":{"bool":{"must":[{"query_string":{"query":"vhost:\"%s\" AND document:*.html AND useragent:mozilla" % domain,"analyze_wildcard":True}},{"range":{"@timestamp":{"gte":"now-30d","lte":"now","format":"epoch_millis"}}}],"must_not":[]}},"size":0,"_source":{"excludes":[]},"aggs":{"uniques":{"date_histogram":{"field":"@timestamp","interval":"1d","time_zone":"Europe/Berlin","min_doc_count":1}}}}        
        res = es.search(index='loggy-*', request_timeout=90, body = query)
        
        arr = [['Date', 'Pageviews']]
        for el in res['aggregations']['uniques']['buckets']:
                d = el['key_as_string'].replace(' 00:00:00', '')
                c = el['doc_count']
                arr.append([d,c])
        book.update({'Pageviews, past month': arr})
        
        
        
        # Get most visited pages
        query = {"query":{"bool":{"must":[{"query_string":{"query":"vhost:\"%s\" AND uri:*.html AND useragent:mozilla" % domain,"analyze_wildcard":True}},{"range":{"@timestamp":{"gte":"now-30d","lte":"now","format":"epoch_millis"}}}],"must_not":[]}},"size":0,"_source":{"excludes":[]},"aggs":{"2":{"terms":{"field":"uri.keyword","size":50,"order":{"_count":"desc"}}}}}
        res = es.search(index='loggy-*', request_timeout=90, body = query)
        
        arr = [['URI', 'Pageviews']]
        for el in res['aggregations']['2']['buckets']:
                d = el['key'].replace(' 00:00:00', '')
                c = el['doc_count']
                arr.append([d,c])
        book.update({'Most visited pages, past month': arr})
        
        
        
        # Geomapping
        query = {"query":{"bool":{"must":[{"query_string":{"query":"vhost:\"%s\" AND useragent:mozilla AND NOT (geo_country.keyword in (\"EU\", \"AP\", \"A1\", \"A2\", \"SX\", \"SS\", \"-\")) AND NOT geo_country.keyword:\"-\"" % domain,"analyze_wildcard":True}},{"range":{"@timestamp":{"gte":"now-30d","lte":"now","format":"epoch_millis"}}}],"must_not":[]}},"size":0,"_source":{"excludes":[]},"aggs":{"2":{"terms":{"field":"geo_country.keyword","size":200,"order":{"_count":"desc"}}}}}
        res = es.search(index='loggy-*', request_timeout=90, body = query)
        
        arr = [['Country', 'Pageviews']]
        for el in res['aggregations']['2']['buckets']:
                d = el['key']
                c = el['doc_count']
                arr.append([d,c])
        book.update({'Geomapping, past month': arr})
        
        
        pyexcel_ods.save_data("/var/www/snappy/exports/%s.ods" % domain, book)

domains = open("/var/www/snappy/domains.txt").read().split()
for sdomain in domains:
        if sdomain:
                makeBook(sdomain)
