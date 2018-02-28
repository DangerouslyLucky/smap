"""
@author: Scott Cuthbert <scottc.engineer@gmail.com>

[changelog]

??-??-????  -   I forget when I first made this.

[pending updates]

Make script clock under 5s for a /24
Figure out -sf, or make args[0] pull input?
Better user input checking/error handling, as always
Fix globals issue to clean up ping_check function arguments
Clean up imports
Figure out if the script is wasting time pinging network and broadcast adds
Add features?

"""

import platform
import subprocess
import argparse
import ipaddress
import multiprocessing
import socket

needShell = False
pingArg = ""
fqdn = False
findOffline = False


def main():

    windows_check()
    args = parser()

    # wacky user input checking
    try:
        subnet = ipaddress.ip_network(args.IP)
        num = subnet.num_addresses
    except Exception as msg:  # would ValueError be better?
        print("\nError: %s\nPlease check inputs and try again.\n" % msg)
        exit()

    if args.FQDN:
        global fqdn
        fqdn = True
    if args.OFFLINE:
        global findOffline
        findOffline = True

    # find out if it actually spawns this many
    print("Spawning %s processes to sweep subnet %s" % (num, subnet))

    report = multi_echo(subnet, findOffline)
    if findOffline:
        print("Report of OFFLINE hosts:\n")
    else:
        print("Report of online hosts:\n")
    for item in report:
        if item != "":  # TODO fix code so this isn't necessary
            print(item)


# TODO figure out why my globals are fucky
# create subprocess to ping check host, return result
def ping_check(host, pingArg, fqdn, offline, send_end):

    command = ("ping %s %s" % (pingArg, host))
    out = subprocess.run(command, shell=needShell,
                         stdout=subprocess.PIPE).returncode
    hostn = socket.gethostbyaddr

    if offline:
        if out == 1:  # returncode NOT ZERO for a failed ping
            name = ""
            if fqdn:
                try:
                    name = hostn(str(host))
                    name = ("\t| %s" % name[0])
                except Exception:
                    name = ("\t| ")
            result = ("%s%s" % (host, name))
        else:
            result = ""
    else:
        if out == 0:  # returncode 0 for successful ping
            name = ""
            if fqdn:  # attempt to look up hostname
                try:
                    name = hostn(str(host))  # do I need to type this to str?
                    name = ("\t| %s" % name[0])
                except Exception:  # really dude?
                    name = ("\t| ")
            result = ("%s%s" % (host, name))
        else:
            result = ""

    send_end.send(result)


# spawn a ping_check function process for each host in subnet
def multi_echo(subnet, off):

    jobs = []
    outlist = []
    magic = multiprocessing.Process

    for host in subnet.hosts():
        recv_end, send_end = multiprocessing.Pipe(False)
        p = magic(target=ping_check, args=(host, pingArg, fqdn, off, send_end))
        jobs.append(p)
        outlist.append(recv_end)
        p.start()

    # [p.join() for p in jobs]

    results = [item.recv() for item in outlist]

    return results


# TODO figure out how to make -sf work
# create the parser and return args
def parser():

    # Create the  parser
    parser = argparse.ArgumentParser(description=(
        'Scott Cuthbert - Smap'))
    # -s specifies a subnet
    parser.add_argument('-s', dest='IP', nargs='?',
                        action='store', help='Sweep a subnet')
    # -f turns on hostname lookups
    parser.add_argument('-f', dest='FQDN', action='store_true',
                        default=False, help='Return FQDNs')
    # -o flags for finding offline hosts
    parser.add_argument('-o', dest='OFFLINE', action='store_true',
                        default=False, help="Return nodes that don't respond")
    args = parser.parse_args()

    return args


# set appropriate shell and ping arguments per platform
def windows_check():

    global needShell
    global pingArg

    if platform.system().lower() == "windows":
        needShell = False
        pingArg = "-n 1"
    else:
        needShell = True
        pingArg = "-c 1"


if __name__ == '__main__':
    main()
