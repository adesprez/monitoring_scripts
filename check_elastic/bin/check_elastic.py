#!/usr/bin/env python

""" check_elastic.py: check general state of Elasticsearch cluster and print some metrics"""

"""
This script will check Elasticsearch cluster availability and print some metrics with the following format:
metric_name=metric_value

This script was originally intended to be used by vmWare's Hyperic monitoring system.

Prerequisites:
- python >= 2.6
- python-requests
- PyYAML

Compatibility :
- Elasticsearch : 1.4, 1.5, 1.6, 1.7, 2.0, 2.1, 2.2, 2.3
- Python : 2.6, 2.7, 3.4
- Tested on CentOS 6.7

You must create the file /etc/hostname.short in order to be able to apply per server configuration

Usage: ./check_elastic.py

"""

__author__  = "Adrien Desprez"
__email__   = "adrien.desprez@gmail.com"
__license__ = "GPL"
__version__ = "1.0"

import requests
import yaml
import os
from distutils.version import LooseVersion
import sys
import json

# Loading hyperic config file, general config file and specific config file
config = {}

try:
    script_path = sys.path[0]
    general_config_file = '%s/../etc/check_elastic.yml' % script_path
    hyperic_config_file = '%s/../etc/check_hyperic.yml' % script_path
    if os.path.exists(general_config_file):
        with open(general_config_file, 'r') as f:
            general_config = yaml.load(f)
            config.update(general_config)
    if os.path.exists(hyperic_config_file):
        with open(hyperic_config_file, 'r') as f:
            hyperic_config = yaml.load(f)
            config.update(hyperic_config)

    if os.path.exists('/etc/hostname.short'):
        f = open('/etc/hostname.short')
        hostname = f.readline().strip()
        specific_config_file = '%s/../etc/%s/check_elastic.yml' % (script_path, hostname)
        if os.path.exists(specific_config_file):
            with open(specific_config_file, 'r') as f:
                config_specific = yaml.load(f)
                config.update(config_specific)
except Exception as e:
    print("Unknown\nCan't load configuration files: %s" % (str(e)))
    # Can't return appropriate exit code since we can't read the configuration (3 = unknown)
    exit(int(config['health_map']['unknown']))


def get_json(uri):
    try:
        r = requests.get(uri)
        return r.json()

    except requests.exceptions.ConnectionError as e:
        print("Critical\n%s" % (str(e)))
        exit(int(config['health_map']('critical')))

    except requests.exceptions.HTTPError as e:
        print("Unknown\nInvalid HTTP response\n\n%s" % (str(e)))
        exit(int(config['health_map']['unknown']))

    except requests.exceptions.Timeout as e:
        print("Unknown\nTimeout request\n\n%s" % (str(e)))
        exit(int(config['health_map']['unknown']))


def get_http(uri):
    try:
        r = requests.get(uri)
        return r.text.rstrip()

    except requests.exceptions.ConnectionError as e:
        print("Critical\n%s" % (str(e)))
        exit(int(config['health_map']('critical')))

    except requests.exceptions.HTTPError as e:
        print("Unknown\nInvalid HTTP response\n\n%s" % (str(e)))
        exit(int(config['health_map']['unknown']))

    except requests.exceptions.Timeout as e:
        print("Unknown\nTimeout request\n\n%s" % (str(e)))
        exit(int(config['health_map']['unknown']))


def bytes_to_gbytes(s):
    return float(s) / 1024 / 1024 / 1024


def to_percent(s):
    return float(s) / 100


def es_main_state():
    main_state = get_http(r'http://%s:%s/_cat/health?h=status' %
                          (config['host'], config['port']))

    if not main_state:
        exit(int(config['health_map']['unknown']))

    if main_state != "green":
        exit(int(config['health_map'][config['health_map_elastic'][main_state]]))

    exit(int(config['health_map']['ok']))


def es_nodes():
    es_health = get_json(r'http://%s:%s/_cluster/health' % (config['host'], config['port']))
    print("number_of_nodes=" + str(es_health.get('number_of_nodes')))


def es_data_nodes():
    es_health = get_json(r'http://%s:%s/_cluster/health' % (config['host'], config['port']))
    print("number_of_data_nodes=" + str(es_health.get('number_of_data_nodes')))


def es_active_shards():
    es_health = get_json(r'http://%s:%s/_cluster/health' % (config['host'], config['port']))
    print("active_shards=" + str(es_health.get('active_shards')))


def get_node_id():
    nodes_stats = get_json(r'http://%s:%s/_nodes/_local/stats' % (config['host'], config['port']))

    return list(nodes_stats['nodes'].keys())[0]


def get_elastic_version():
    elastic_version = get_http(r'http://%s:%s' % (config['host'], config['port']))
    elastic_version_json = json.loads(elastic_version)
    return elastic_version_json['version']['number']


def es_cache():

    for cache in config['caches']:
        try:
            cache_json = get_json(r'http://%s:%s/%s' % (config['host'], config['port'], config['caches'][cache]))
            print("%s_size=%s" % (cache, cache_json["_all"]["total"][cache]["memory_size_in_bytes"]))
        except KeyError:
            print("%s_size=N/A" % cache)


# Node JVM
def es_jvm(node_id):
    es_jvm = get_json(r'http://%s:%s/_nodes/_local/stats/jvm' % (config['host'], config['port']))
    jvm_mem = es_jvm['nodes'][node_id]['jvm']['mem']
    jvm_mem_pools = es_jvm['nodes'][node_id]['jvm']['mem']['pools']
    jvm_gc = es_jvm['nodes'][node_id]['jvm']['gc']['collectors']
    print("heap_used_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem['heap_used_in_bytes'])))
    print("heap_used_percent=" + str(to_percent(float(jvm_mem['heap_used_percent']))))
    print("heap_committed_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem['heap_committed_in_bytes'])))
    print("heap_max_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem['heap_max_in_bytes'])))
    print("pools_young_used_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem_pools['young']['used_in_bytes'])))
    print("pools_young_max_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem_pools['young']['max_in_bytes'])))
    print("pools_survivor_used_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem_pools['survivor']['used_in_bytes'])))
    print("pools_survivor_max_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem_pools['survivor']['max_in_bytes'])))
    print("pools_old_used_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem_pools['old']['used_in_bytes'])))
    print("pools_old_max_in_Gbytes=" + str(bytes_to_gbytes(jvm_mem_pools['old']['max_in_bytes'])))
    print("gc_young_collection_count=" + str(jvm_gc['young']['collection_count']))
    print("gc_young_collection_time_in_millis=" + str(jvm_gc['young']['collection_time_in_millis']))
    print("gc_old_collection_count=" + str(jvm_gc['old']['collection_count']))
    print("gc_old_collection_time_in_millis=" + str(jvm_gc['old']['collection_time_in_millis']))


# Node process
def es_process(node_id, elastic_version):
    es_process = get_json(r'http://%s:%s/_nodes/_local/stats/process' % (config['host'], config['port']))['nodes'][node_id]['process']
    try :
        print("process_cpu_percent=" + str(to_percent(es_process['cpu']['percent'])))
    except KeyError:
        print("process_cpu_percent=N/A")

    if LooseVersion(elastic_version) < LooseVersion('2.0.0'):
        try:
            print("process_mem_resident_in_Gbytes=" + str(bytes_to_gbytes(es_process['mem']['resident_in_bytes'])))
        except KeyError:
            print("process_mem_resident_in_Gbytes=N/A")
    else:
        try:
            print("process_mem_virtual_in_Gbytes=" + str(bytes_to_gbytes(es_process['mem']['total_virtual_in_bytes'])))
        except KeyError:
            print("process_mem_virtual_in_Gbytes=N/A")


# Node indices
def es_indices(node_id):
    es_indices = get_json(r'http://%s:%s/_nodes/_local/stats/indices' % (config['host'], config['port']))['nodes'][node_id]['indices']
    print("docs_count=" + str(es_indices['docs']['count']))
    print("docs_deleted=" + str(es_indices['docs']['deleted']))
    print("store_size_in_Gbytes=" + str(bytes_to_gbytes(es_indices['store']['size_in_bytes'])))
    print("store_throttle_time_in_millis=" + str(es_indices['store']['throttle_time_in_millis']))
    print("index_total=" + str(es_indices['indexing']['index_total']))
    print("index_time_in_millis=" + str(es_indices['indexing']['index_time_in_millis']))
    print("index_current=" + str(es_indices['indexing']['index_current']))
    print("get_total=" + str(es_indices['get']['total']))
    print("get_time_in_millis=" + str(es_indices['get']['time_in_millis']))
    print("search_open_contexts=" + str(es_indices['search']['open_contexts']))
    print("search_query_total=" + str(es_indices['search']['query_total']))
    print("search_query_time_in_millis=" + str(es_indices['search']['query_time_in_millis']))
    print("merges_current=" + str(es_indices['merges']['current']))
    print("merges_current_docs=" + str(es_indices['merges']['current_docs']))
    print("merges_current_size_in_bytes=" + str(es_indices['merges']['current_size_in_bytes']))
    print("merges_total=" + str(es_indices['merges']['total']))
    print("fielddata_evictions=" + str(es_indices['fielddata']['evictions']))
    print("segments_count=" + str(es_indices['segments']['count']))
    print("segments_memory_in_Gbytes=" + str(bytes_to_gbytes(es_indices['segments']['memory_in_bytes'])))


def main():
    node_id = get_node_id()
    elastic_version = get_elastic_version()
    es_nodes()
    es_data_nodes()
    es_active_shards()
    es_jvm(node_id)
    es_process(node_id, elastic_version)
    es_indices(node_id)
    es_cache()
    es_main_state()


if __name__ == '__main__':
    main()
