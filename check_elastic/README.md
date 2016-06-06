
# Overview

This script will check the availability of Elasticsearch cluster and print some metrics with the following format:
with the following format:
```
metric_name=metric_value
```

This script was originally intended to be used by vmWare's Hyperic monitoring system. This script was tested on
Elasticsearch version: 1.4, 1.5, 1.6, 1.7, 2.0, 2.1, 2.2, 2.3 and is compatible with Python version: 2.6, 2.7, 3.3.

# Prerequisites

- PyYAML library in order to parse the configuration files
- python-requests

You must create the file `/etc/hostname.short` in order to be able to apply per server configuration (see Configuration
by machine section below)


# Script install and usage

Copy the `check_elastic` directory on a server able to reach an Elasticsearch running node.

Then, run it:
```bash
./check_elastic.py
```

## Configuration by machine

Every parameter in YAML files can be overloaded by a specific, per machine, configuration.

In order to use per machine configuration, you shall create a file named `/etc/hostname.short` that contain the hostname
you want to match in `etc` directory.

Assuming you have two machines running Elasticsearch: *host1* and *host2*. *host1* and *host2* Elasticsearch instances
don't bind on the same IP/port.

file tree:
```
check_elastic
    bin
        check_elastic.py
    etc
        host1
            check_elastic.yml   # specific configuration file for host1
        host2
            check_elastic.yml   # specific configuration file for host2
        check_elastic.yml       # generic configuration file   
```

*host1* specific configuration file:
```yaml
host : '127.0.0.2'
port : '9202'
```

Also, *host1* must have a file named `/etc/hostname.short` containing the name of the machine: host1

*host2* specific configuration file:
```yaml
host : '127.0.0.3'
port : '9203'
```

Also, *host2* must have a file named `/etc/hostname.short` containing the name of the machine: host2

Generic configuration file:
```yaml
host : '127.0.0.1'
port : '9200'

health_map_elastic :
  green: 'ok'
  yellow: 'warning'
  red: 'critical'

valid_options: ['general','nodes','data_nodes','shards']

caches :
  filter_cache: '_stats/filter_cache'
  id_cache: '_stats/id_cache'
  fielddata: '_stats/fielddata'
  percolate: '_stats/percolate'
  query_cache: '_stats/query_cache'
```

The `host` and `port` parameters of the generic configuration file will be overloaded by respective server's specific
configuration file.

# Hyperic integration

This script was written in order to graph elastic stats on vmWare's Hyperic monitoring system.

You can find on `lib` directory an example of an Hyperic plugin (*elastic-plugin.xml*) that can use the 
*check_elastic.py* script to graph some key metrics of elastic stats.


# Changelog

1.0 : Initial version