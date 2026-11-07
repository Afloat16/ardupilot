#!/usr/bin/env python3

# flake8: noqa

'''
playback a capture from ardupilot with timing
the file format is a sequence of:

  HEADER
  DATA

HEADER is:
   uint32_t magic == 0x7fe53b04
   uint32_t time_ms
   uint32_t length
'''

import socket
import time
import struct
from argparse import ArgumentParser

parser = ArgumentParser(description="playback a capture file with ArduPilot timing headers")

parser.add_argument("infile", default=None, help="input file")
parser.add_argument("dest", default=None, help="TCP destination in ip:port format")
parser.add_argument("--loop", action='store_true', help="loop to start of file at EOF")
args = parser.parse_args()

def open_socket(dest):
    a = dest.split(':')
    ip = a[0]
    port = int(a[1])
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect((ip, port))
    return tcp

f = open(args.infile,'rb')
tcpsock = open_socket(args.dest)

last_ms = None

while True:
    hdr_raw = f.read(12)
    if not hdr_raw:
        if args.loop and last_ms is not None:
            f.seek(0)
            last_ms = None
            continue
        print("EOF")
        break
    if len(hdr_raw) != 12:
        parser.exit(1, "Truncated capture header\n")
    magic, t_ms, n = struct.unpack("<III", hdr_raw)
    if magic != 0x7fe53b04:
        parser.exit(1, "Bad capture magic\n")
    data = f.read(n)
    if len(data) != n:
        parser.exit(1, "Truncated capture data\n")
    if last_ms is not None:
        dt = t_ms - last_ms
        if dt > 0:
            time.sleep(dt*0.001)
    last_ms = t_ms
    tcpsock.sendall(data)
    print("Wrote %u bytes t=%.3f" % (len(data), t_ms*0.001))
