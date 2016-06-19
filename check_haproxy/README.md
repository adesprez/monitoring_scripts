
# Overview

This script will check the general state of HAproxy, state of individual servers and list HAproxy stats
with the following format:
```
metric_name=metric_value
```

This script was originally intended to be used by vmWare's Hyperic monitoring system. This script was tested on
HAproxy 1.5. This script is compatible with Python 2.6, 2.7, 3.3.

# Prerequisites

- PyYAML library in order to parse the configuration files
- socat command line to get HAproxy stats
- sudo capable account to be able to read on HAproxy stats socket

You must create the file `/etc/hostname.short` in order to be able to apply per server configuration (see Configuration
by machine section below)


# HAproxy configuration

HAproxy must be configured to publish stats on an Unix socket, this is done on the *global* section.

HAproxy configuration example:
```
global
    # [...]
    stats socket /var/lib/haproxy/stats
    # [...]
```


# Script install and usage

Copy the `check_haproxy` directory on the server running HAproxy.

Be sure to match the parameter *haproxy_stat_socket* on `etc/check_haproxy.yml` with the configuration of HAproxy
*stats socket*.

Then, run it:
```bash
./check_haproxy.py
```

## HAproxy servers exclusion

The script will, by default, check every HAproxy servers state. If one server state is 'DOWN', the script will end
with an error code.
May be some servers of some backends are not important and we don't want the script to check them.

You can exclude HAproxy servers from being checked by putting their name on the list *servers_exclude*

HAproxy example configuration
```
backend image-backend
    server image1 192.168.69.2:83 check
    server image2 192.168.69.2:84 check
    server image3 192.168.69.2:85 check
    server image4 192.168.69.2:86 check
```

We don't want the script to fail if the servers *image3* or *image4* are down.

On `check_haproxy.yml`:
```yaml
servers_exclude                 : ['image3', 'image4']
```

## Configuration by machine

Every parameter in YAML files can be overloaded by a specific, per machine, configuration.

In order to use per machine configuration, you shall create a file named `/etc/hostname.short` that contain the hostname
you want to match in `etc` directory.

Assuming you have two machines running HAproxy: *host1* and *host2*. You want to exclude the HAproxy server *image4*
to be checked on *host1* and the server *ssl5* to be checked on *host2*.

file tree:
```
check_haproxy
    bin
        check_haproxy.py
    etc
        host1
            check_haproxy.yml   # specific configuration file for host1
        host2
            check_haproxy.yml   # specific configuration file for host2
        check_haproxy.yml       # generic configuration file   
```

*host1* specific configuration file:
```yaml
servers_exclude                 : ['image4']
```

Also, *host1* must have a file named `/etc/hostname.short` containing the name of the machine: host1

*host2* specific configuration file:
```yaml
servers_exclude                 : ['ssl5']
```

Also, *host2* must have a file named `/etc/hostname.short` containing the name of the machine: host2

Generic configuration file:
```yaml
haproxy_stat_socket             : '/var/lib/haproxy/stats'
```

# Hyperic integration

This script was written in order to graph HAproxy stats on vmWare's Hyperic monitoring system.

You can find on `lib` directory an example of an Hyperic plugin (*haproxy-plugin.xml*) that can use the *check_haproxy.py* script to
graph some key metrics of HAproxy stats.


# Changelog

1.0 : Initial version