#!/usr/bin/env python3
import sys
import os
import re
import time
import uuid
import json
import smtplib

def run_check():
    eml = sys.stdin.read()
    m = re.search(r"ID: (\S+) TIMESTAMP: (\d+)", eml)
    if m:
        id = m.group(1)
        ts = int(m.group(2))
        diff = time.time() - ts
        js = json.load(open("/var/www/html/probes.json", "r"))
        if id in js:
            js[id]['delivered'] = time.time()
            js[id]['delay'] = diff
            with open("/var/www/html/probes.json", "w") as f:
                json.dump(js, f, indent = 2)
                f.close()

def send_probe():
    server = smtplib.SMTP('mx1-lw-us.apache.org')
    emlid = "<%s@mbox-vm.apache.org>" % str(uuid.uuid4())
    msg = "From: probe@mbox-vm.apache.org\r\nMessage-ID: %s\r\nTo: roundtrip@apache.org\r\nSubject: Roundtrip Test\r\n\r\nID: %s TIMESTAMP: %u\r\n" % (emlid, emlid, time.time())
    server.sendmail('probe@mbox-vm.apache.org', ['roundtrip@apache.org'], msg)
    server.quit()
    js = json.load(open("/var/www/html/probes.json", "r"))
    
    js[emlid] = {
        'timestamp': time.time(),
    }
    with open("/var/www/html/probes.json", "w") as f:
        json.dump(js, f, indent = 2)
        f.close()

def www():
    bads = 0
    out = ""
    now = time.time()
    js = json.load(open("/var/www/html/probes.json", "r"))
    x = 0
    y = 0
    for id, el in js.items():
        if el['timestamp'] > (now - 86400):
            if 'delay' in el:
                x += el['delay']
                y += 1
            if not 'delay' in el and el['timestamp'] < (now - 900):
                bads += 1
                out += "Message %s was sent at %u (%u seconds ago) but hasn't been delivered yet!\n" % (id, el['timestamp'], now - el['timestamp'])
            elif 'delay' in el and el['delay'] > 600:
                bads += 1
                out += "Message %s was sent at %u, but took %u seconds to be delivered!\n" % (id, el['timestamp'], el['delay'])
    if not bads:
        print("Status: 200 Okay\r\nContent-Type: text/plain\r\n\r\n")
        print("Roundtrips for the past 24 hours are all okay\r\n")
        if y > 0:
            print("Average delay:%u seconds" % (x/y))
    else:
        print("Status: 500 Roundtrip errors detected\r\nContent-Type: text/plain\r\n\r\n")
        print(out)

if len(sys.argv) > 1 and sys.argv[1] == 'check':
    run_check()
elif len(sys.argv) > 1 and sys.argv[1] == 'probe' :
    send_probe()
else:
    www()
