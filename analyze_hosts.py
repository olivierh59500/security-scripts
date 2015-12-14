#!/usr/bin/env python

"""
analyze_hosts -scans one or more hosts for security misconfigurations

Copyright (C) 2015 Peter Mosmans [Go Forward]
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
import subprocess
import sys
import textwrap


import nmap


UNKNOWN = -1


def print_error(text, options, result):
    """
    Prints error message and exits with result code result if not 0.
    """
    if not options['quiet']:
        print('[-] ' + text, file=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
    if result:
        sys.exit(result)


def print_status(text, options):
    """
    Prints status message.
    """
    if not options['quiet']:
        print('[*] ' + text)
        sys.stdout.flush()
        sys.stderr.flush()


def preflight_checks(options):
    """
    Checks if all tools are there, and disables tools automatically
    """
    tools = []
    for tool in ['nmap', 'nikto', 'testssl.sh', 'curl']:
        if options[tool]:
            print_status('Checking {0}... '.format(tool), options)
            result, _stdout, _stderr = execute_command([tool, '--version'], options)
            if not result:
                print_error('FAILED: Could not execute {0}, disabling checks'.format(tool), options, False)
                options[tool] = False
            else:
                print_status('OK', options)


def execute_command(cmd, options):
    """
    Executes command.
    Returns True if command succeeded
    """
    stdout = ''
    stderr = ''
    result = False
    if options['dryrun']:
        print_status(' '.join(cmd), options)
        return True, stdout, stderr
    try:

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        result = not process.returncode
    except OSError as exception:
        pass
#        print('could not execute {0}'.format(cmd))
#        print('[-] {0}'.format(exception.strerror), file=sys.stderr)
#    if not result:
#        print_error('FAILED', options, False)
    return result, stdout, stderr


def perform_recon(host, options, output_file):
    """
    Performs all recon actions on @host when specified in @options.
    Writes output to @output_file.
    """
    if options['whois']:
        do_whois(host, options, host_data)
# show output


def do_portscan(host, options, output_file):
    """
    Performs a portscan.


    Returns:
        A list of open ports.

    Arguments:
        host: target host in string
        options: dictionary with options
        output_file: raw output file
    """
    if not options['nmap']:
        # even if nmap is not selected, use it to try to scan open ports first
        return [UNKNOWN]
    open_ports = []
    try:
        arguments = '-A -oN ' + output_file
        if options['allports']:
            arguments += ' -p1-65535 --script=(default or discovery or version) and not broadcast and not external and not intrusive and not http-email-harvest and not http-grep and not ipidseq and not path-mtu and not qscan)'
        if options['trace']:
            arguments += ' --script http-trace'
        if options['dryrun']:
            print_status('nmap ' + arguments, options)
            return [UNKNOWN]
        print_status('starting nmap scan', options)
        scanner = nmap.PortScanner()
        scanner.scan(hosts=host, arguments=arguments)
        print_status('Finished succesfully')
        for ip in scanner.all_hosts():
            if scanner[ip] and scanner[ip].state() == 'up':
                for protocol in scanner[ip].all_protocols():
                    for port in scanner[ip][protocol].keys():
                        if scanner[ip][protocol][port]['state'] == "open":
                            open_ports.append(port)
        print_status('Found open ports {0}'.format(open_ports), options)
    except nmap.PortScannerError:
        return [UNKNOWN]
    return open_ports

# All checks



def append_logs(output_file, stdout, stderr):
    if stdout:
        with open(output_file, "a") as open_file:
            open_file.write(stdout)
    if stderr:
        with open(output_file, "a") as open_file:
            open_file.write(stderr)


def reverse_lookup(ip):
    """
    Resolves an IP address to a hostname
    """
    return socket.gethostbyaddr(ip)

# tool-specific commands

def do_curl(host, port, options, output_file):
    """Checks for HTTP TRACE method
    
    Returns:
    
    Arguments:
        host: 
        port: port that needs to be scanned
        options: 
        output_file: 
    """
    if options['trace']:
        command = ['curl', '-qsIA', "'{0}'".format(options['header']), '--connect-timeout', str(options['timeout']), '-X', 'TRACE', '{0}:{1}'.format(host, port)]
        result, stdout, stderr = execute_command(command, options)
        append_logs(output_file, stdout, stderr)


def do_nikto(host, port, options, output_file):
    """Performs a nikto scan.

    Arguments:
        host:
        options:
        output_file:
    """
    command = ['nikto', '-display', 'P', '-u', '{0}:{1}'.format(host, port)]
    if port == 443:
        command.append('-ssl')
    result, stdout, stderr = execute_command(command, options)
    append_logs(output_file, stdout, stderr)


def do_testssl(host, port, options, output_file):
    """Checks for SSL/TLS configuration
    
    Returns:
    
    Arguments:
        host: 
        port: port that needs to be scanned
        options: 
        output_file: 
    """
    command = ['testssl.sh', '--color', '0', '{0}:{1}'.format(host, port)]
    result, stdout, stderr = execute_command(command, options)
    append_logs(output_file, stdout, stderr)


def interrogate_DNS(ip):
    """Performs deeper DNS inspection.

    Arguments:
        ip: ip address
    """
    reverse = dns.reversename.from_address(ip)
    print(reverse)

    
def prepare_queue(options):
    """Prepares a queue file which holds all hosts to scan.
    """
    return


def remove_from_queue(host, queue):
    """
    Removes a host from the queue file.
    """
    queuefile = 'analyze_hosts.queue'
    
    return 'analyze'


def port_open(port, open_ports):
    """
    Checks whether a port has been flagged as open
    Returns True if the port was open, or hasn't been scanned.

    Arguments:
    - `port`: the port to look up
    - `open_ports`: a list of open ports, or -1 if it hasn't been scanned.
    """
    return (UNKNOWN in open_ports) or (port in open_ports)


def use_tool(tool, host, port, options, output_file):
    if not options[tool]:
        return
#    print_status('using tool {0}'.format(tool), options)
    if tool == 'nikto':
        do_nikto(host, port, options, output_file)
    if tool == 'curl':
        do_curl(host, port, options, output_file)
    if tool == 'testssl.sh':
        do_testssl(host, port, options, output_file)



def loop_hosts(options, queue):
    """
    """
    for host in queue:
        output_file = '{0}.analyze_hosts'.format(host)
        perform_recon(host, options, output_file)
        open_ports = do_portscan(host, options, output_file)
        for port in [80, 443, 8080]:
            if port_open(port, open_ports):
                for tool in ['curl', 'nikto']:
                    use_tool(tool, host, port, options, output_file)
                if port == 443:
                    for tool in ['testssl.sh']:
                        use_tool(tool, host, port, options, output_file)
#        if port_open(53, open_ports):
#            recursive_dig(host, options, host_data, output_file)
        remove_from_queue(host, queue)


def parse_arguments():
    """
    Parses command line arguments.
    """
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent('''\
analyze_hosts

Copyright (C) 2015 Peter Mosmans [Go Forward]
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.'''))
    parser.add_argument('target', nargs='?', type=str,
                        help='[TARGET] can be a single (IP) address, an IP range, eg. 127.0.0.1-255, or multiple comma-separated addressess')
    parser.add_argument('--dryrun', action='store_true',
                        help='only show commands, don\'t actually run anything')
    parser.add_argument('-i', '--inputfile', action='store', type=str,
                        help='a file containing multiple targets, one per line')
    parser.add_argument('-f', '--force', action='store_true',
                        help='don\'t perform preflight checks, go ahead anyway')
    parser.add_argument('--nikto', action='store_true',
                        help='run a nikto scan')
    parser.add_argument('-p', '--nmap', action='store_true',
                        help='run a nmap scan')
    parser.add_argument('--ssl', action='store_true',
                        help='run a ssl scan')    
    parser.add_argument('--allports', action='store_true',
                        help='run a full-blown nmap scan on all ports')
    parser.add_argument('-t', '--trace', action='store_true',
                        help='check webserver for HTTP TRACE method')
    parser.add_argument('-w', '--whois', action='store_true',
                        help='perform a whois lookup')
    parser.add_argument('--header', action='store', default='analyze_hosts',
                        help='custom header to use for scantools (default analyze_hosts)')
    parser.add_argument('--timeout', action='store', default='10', type=int,
                        help='timeout for requests in seconds (default 10)')
    parser.add_argument('--quiet', action='store_true', 
                        help='Don\'t output status messages')
    args = parser.parse_args()
    if not (args.inputfile or args.target):
        parser.error('Specify either a target or input file')
    options = vars(parser.parse_args())
    options['nmap'] = (args.allports | args.nmap)
    options['testssl.sh'] = args.ssl
    options['curl'] = args.trace
    return options


def main():
    """
    Main program loop.
    """
    options = parse_arguments()
    queue = []
    if not options['force']:
        preflight_checks(options)
    if not options['inputfile']:
        queue.append(options['target'])
    loop_hosts(options, queue)


if __name__ == "__main__":
    main()
