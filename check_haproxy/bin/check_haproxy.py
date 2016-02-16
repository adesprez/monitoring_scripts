#!/usr/bin/env python

""" check_haproxy.py: check general state of HAproxy, state of individual servers and list HAproxy stats"""

"""

This script will check the general state of HAproxy, state of individual servers and list HAproxy stats
with the following format:
metric_name=metric_value

This script was originally intended to be used by vmWare's Hyperic monitoring system.

Prerequisites:
- PyYAML library in order to parse the configuration files
- socat command line to get HAproxy stats
- sudo capable account to be able to ready on HAproxy stats socket

You must create the file /etc/hostname.short in order to be able to apply per server configuration

Usage: ./check_haproxy.py

"""

__author__  = "Adrien Desprez"
__email__   = "adrien.desprez@gmail.com"
__license__ = "GPL"
__version__ = "1.0"

import os
import sys
import yaml
from subprocess import Popen, PIPE

# Loading hyperic config file, general config file and specific config file
try:
    script_path = sys.path[0]
    hyperic_config_file = '%s/../etc/check_hyperic.yml' % script_path
    general_config_file = '%s/../etc/check_haproxy.yml' % script_path
    with open(hyperic_config_file, 'r') as f:
        config = yaml.load(f)
    if os.path.exists(general_config_file):
        with open(general_config_file, 'r') as f:
            general_config = yaml.load(f)
            config = dict(config.items() + general_config.items())

    if os.path.exists('/etc/hostname.short'):
        f = open('/etc/hostname.short')
        hostname = f.readline().strip()
        specific_config_file = '%s/../etc/%s/check_haproxy.yml' % (script_path, hostname)
        if os.path.exists(specific_config_file):
            with open(specific_config_file, 'r') as f:
                config_specific = yaml.load(f)
                config = dict(config.items() + config_specific.items())
except Exception, e:
    print "Unknown\nCan't load configuration files: %s" % (str(e))
    # Can't return appropriate exit code since we can't read the configuration
    exit(config['health_map']['unknown'])


def ha_global_stats():
    """
    Get global HAproxy stats form Unix socket
    """
    try:
        command = 'echo "show info" |sudo socat unix-connect:%s stdio' % config['haproxy_stat_socket']
        process = Popen(args=command, stdout=PIPE, shell=True)
        global_infos_raw = process.communicate()[0].replace(' ', '')
    except Exception as e:
        print "Critical\nCould not get HAproxy stats: %s" % (str(e))
        exit(int(config['health_map']['critical']))

    # Remove 2 last lines which are empty
    global_infos_raw2 = global_infos_raw[:global_infos_raw.rfind('\n\n')]

    # String to dictionnary conversion
    global_infos_dict = dict(x.split(':') for x in global_infos_raw2.split('\n'))
    for metric, value in global_infos_dict.iteritems():
        print "%s=%s" % (metric, value)


def ha_main_state():
    """
    Get HAproxy main state
    """
    try:
        command = 'echo "show info" |sudo socat unix-connect:%s stdio' % config['haproxy_stat_socket']
        process = Popen(args=command, stdout=PIPE, shell=True)
        result = process.communicate()[0]
        if result is None or result == '':
            print "Critical\nCould not get HAproxy stats"
            exit(int(config['health_map']['critical']))
    except Exception as e:
        print "Critical\nCould not get HAproxy stats: %s" % (str(e))
        exit(int(config['health_map']['critical']))


def discover_ha_frontends_backends_servers():
    """
    Discover HAproxy frontends, backends and servers.
    :return: dictionary of frontends, backends and servers
    """

    try:
        command = 'echo "show stat" |sudo socat unix-connect:%s stdio' % config['haproxy_stat_socket']
        process = Popen(args=command, stdout=PIPE, shell=True)
        result = process.communicate()[0]
    except Exception as e:
        print "Critical\nCould not get HAproxy stats: %s" % (str(e))
        exit(int(config['health_map']['critical']))

    frontends = []
    backends = []
    servers = {}

    # Populate frontends and backends lists
    for line in result.splitlines():
        for element in line.split(','):
            if element == 'FRONTEND':
                frontend_name = line.split(',')[0]
                print "Found frontend %s" % frontend_name
                frontends.append(frontend_name)

            if element == 'BACKEND':
                backend_name = line.split(',')[0]
                print "Found backend %s" % backend_name
                backends.append(backend_name)

    # Populate servers dictionary
    for line in result.splitlines():
        if line.split(',')[0] in backends and line.split(',')[1] != 'BACKEND':
            server_name = line.split(',')[1]
            backend_name = line.split(',')[0]
            print "Found server %s for backend %s" % (server_name, backend_name)
            servers.setdefault(backend_name, []).append(server_name)

    return frontends, backends, servers


def ha_frontends_stats():
    """
    Get HAproxy frontends stats, display stats for each frontends, one metric by line
    frontend-name_metric=metric_value
    """
    try:
        command = 'echo "show stat -1 1 -1" |sudo socat unix-connect:%s stdio' % config['haproxy_stat_socket']
        process = Popen(args=command, stdout=PIPE, shell=True)
        result = process.communicate()[0]
    except Exception as e:
        print "Critical\nCould not get Frontends stats: %s" % (str(e))
        exit(int(config['health_map']['critical']))

    metric_keys = result.splitlines()[0].split(',')
    frontends_lines = result.split("\n", 1)[1].rstrip()

    for frontend_line in frontends_lines.splitlines():
        element_id = 0
        frontend_line_elements = frontend_line.split(',')
        for element in frontend_line_elements:
            try:
                print "%s_%s=%s" % (frontend_line_elements[0], metric_keys[element_id], frontend_line_elements[element_id])
                element_id += 1
            except Exception as e:
                print "%s_%s=%s" % (frontend_line_elements[0], "ERROR", "ERROR")


def ha_backends_stats():
    """
    Get HAproxy backends stats, display stats for each backends, one metric by line
    backend-name_metric=metric_value
    """
    try:
        command = 'echo "show stat -1 2 -1" |sudo socat unix-connect:%s stdio' % config['haproxy_stat_socket']
        process = Popen(args=command, stdout=PIPE, shell=True)
        result = process.communicate()[0]
    except Exception as e:
        print "Critical\nCould not get Backends stats: %s" % (str(e))
        exit(int(config['health_map']['critical']))

    metric_keys = result.splitlines()[0].split(',')
    backends_lines = result.split("\n", 1)[1].rstrip()

    for backend_line in backends_lines.splitlines():
        element_id = 0
        backend_line_elements = backend_line.split(',')
        for element in backend_line_elements:
            try:
                print "%s_%s=%s" % (backend_line_elements[0], metric_keys[element_id], backend_line_elements[element_id])
                element_id += 1
            except Exception as e:
                print "%s_%s=%s" % (backend_line_elements[0], "ERROR", "ERROR")


def ha_servers_state():
    """
    Get HAproxy servers stats, display stats for each servers, one metric by line
    server-name_metric=metric_value

    If a server is marked as 'DOWN' and is not excluded to the check, the script will end
    with an error execution code.
    """
    try:
        command = 'echo "show stat -1 4 -1" |sudo socat unix-connect:%s stdio' % config['haproxy_stat_socket']
        process = Popen(args=command, stdout=PIPE, shell=True)
        result = process.communicate()[0]
    except Exception as e:
        print "Critical\nCould not get Servers stats: %s" % (str(e))
        exit(int(config['health_map']['critical']))

    metric_keys = result.splitlines()[0].split(',')
    servers_lines = result.split("\n", 1)[1].rstrip()

    for server_line in servers_lines.splitlines():
        element_id = 0
        server_line_elements = server_line.split(',')
        for element in server_line_elements:
            try:
                if server_line_elements[17] == 'DOWN' and server_line_elements[1] not in config['servers_exclude']:
                    print "Critical\nServer %s is DOWN" % server_line_elements[1]
                    exit(int(config['health_map']['critical']))
                print "%s_%s=%s" % (server_line_elements[1], metric_keys[element_id], server_line_elements[element_id])
                element_id += 1
            except Exception as e:
                print "%s_%s=%s" % (server_line_elements[1], "ERROR", "ERROR")


def main():
    ha_main_state()
    discover_ha_frontends_backends_servers()
    ha_global_stats()
    ha_frontends_stats()
    ha_backends_stats()
    ha_servers_state()


if __name__ == '__main__':
    main()
