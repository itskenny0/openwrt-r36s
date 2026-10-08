#!/usr/bin/env python3
"""Exercise the packaged DHCP and SSH servers on an isolated virtual USB link.

Run with sudo after building. Only this process's network namespace changes;
all fixtures and logs stay in the checkout. No physical interface is touched.
"""
import ipaddress
import json
import os
from pathlib import Path
import select
import socket
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if '--isolated' not in sys.argv:
    subprocess.run(['unshare', '--net', sys.executable, str(Path(__file__).resolve()), '--isolated'], check=True)
    raise SystemExit(0)
rootfs = ROOT / 'build_dir/target-aarch64_cortex-a35_musl/root-rk3326'
work = ROOT / '.work/network-smoke'
work.mkdir(parents=True, exist_ok=True)
qemu = ['qemu-aarch64', '-L', str(rootfs), '-E', 'LD_LIBRARY_PATH=' +
        ':'.join(str(rootfs / p) for p in ('lib', 'usr/lib'))]


def ip(*args):
    subprocess.run(['ip', *args], check=True)


ip('link', 'set', 'lo', 'up')
ip('link', 'add', 'host', 'type', 'veth', 'peer', 'name', 'usb0')
ip('link', 'add', 'br-lan', 'type', 'bridge')
ip('link', 'set', 'usb0', 'master', 'br-lan')
ip('address', 'add', '192.168.77.1/24', 'dev', 'br-lan')
for interface in ('host', 'usb0', 'br-lan'): ip('link', 'set', interface, 'up')
mac = bytes.fromhex(json.loads(subprocess.check_output(['ip', '-j', 'link', 'show', 'host']))[0]['address'].replace(':', ''))
(work / 'dnsmasq.conf').write_text(
    'port=0\ninterface=br-lan\nbind-interfaces\nuser=root\n'
    'dhcp-range=192.168.77.100,192.168.77.249,255.255.255.0,12h\n'
    f'dhcp-leasefile={work}/leases\ndhcp-authoritative\nlog-dhcp\n')
(work / 'leases').unlink(missing_ok=True)
key = work / 'ssh-host-key'
key.unlink(missing_ok=True)
with (work / 'keygen.log').open('w') as log:
    subprocess.run([*qemu, str(rootfs / 'usr/bin/dropbearkey'), '-t', 'ed25519', '-f', str(key)],
                   check=True, stdout=log, stderr=subprocess.STDOUT, timeout=120)
processes = []
logs = []
try:
    for name, command in (
        ('dnsmasq', [*qemu, str(rootfs / 'usr/sbin/dnsmasq'), '--keep-in-foreground', '--log-facility=-',
                     '--conf-file=' + str(work / 'dnsmasq.conf')]),
        ('dropbear', [*qemu, str(rootfs / 'usr/sbin/dropbear'), '-F', '-E', '-p', '192.168.77.1:2222', '-r', str(key)]),
    ):
        log = (work / (name + '.log')).open('w')
        logs.append(log)
        processes.append(subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT))
    deadline = time.monotonic() + 15
    while True:
        if any(p.poll() is not None for p in processes): raise RuntimeError('Server exited; inspect network-smoke logs')
        try:
            with socket.create_connection(('192.168.77.1', 2222), timeout=1) as connection:
                assert connection.recv(128).startswith(b'SSH-2.0-dropbear'), 'Missing SSH protocol greeting'
            break
        except OSError:
            if time.monotonic() >= deadline: raise
            time.sleep(0.1)
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))
    sock.bind(('host', 0))
    xid = 0x52333653

    def send(kind, extra=b''):
        bootp = struct.pack('!BBBBIHH4s4s4s4s16s64s128s', 1, 1, 6, 0, xid, 0, 0x8000,
                            bytes(4), bytes(4), bytes(4), bytes(4), mac + bytes(10), bytes(64), bytes(128))
        payload = bootp + b'\x63\x82\x53\x63\x35\x01' + bytes([kind]) + extra + b'\x37\x03\x01\x03\x06\xff'
        udp = struct.pack('!HHHH', 68, 67, 8 + len(payload), 0) + payload
        header = struct.pack('!BBHHHBBH4s4s', 0x45, 0, 20 + len(udp), 0, 0, 64, 17, 0, bytes(4), b'\xff' * 4)
        checksum = sum(struct.unpack('!10H', header))
        while checksum >> 16: checksum = (checksum & 0xffff) + (checksum >> 16)
        header = header[:10] + struct.pack('!H', ~checksum & 0xffff) + header[12:]
        sock.send(b'\xff' * 6 + mac + b'\x08\x00' + header + udp)

    def receive(kind, request_kind, extra=b''):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            send(request_kind, extra)
            until = time.monotonic() + 1
            while time.monotonic() < until and select.select([sock], [], [], max(0, until - time.monotonic()))[0]:
                frame = sock.recv(2048)
                if len(frame) < 282 or frame[23] != 17: continue
                offset = 14 + (frame[14] & 15) * 4
                if frame[offset:offset+4] != struct.pack('!HH', 67, 68): continue
                reply = frame[offset+8:]
                if reply[0] != 2 or reply[4:8] != struct.pack('!I', xid): continue
                options, i = {}, 240
                while i < len(reply) and reply[i] != 255:
                    code = reply[i]
                    if code == 0: i += 1; continue
                    length = reply[i+1]
                    options[code] = reply[i+2:i+2+length]
                    i += length + 2
                if options.get(53) == bytes([kind]): return reply[16:20], options
        raise RuntimeError(f'DHCP message {kind} did not arrive; inspect dnsmasq.log')

    offered, options = receive(2, 1)
    assert int(ipaddress.IPv4Address('192.168.77.100')) <= int(ipaddress.IPv4Address(offered)) <= int(ipaddress.IPv4Address('192.168.77.249'))
    assert options[54] == socket.inet_aton('192.168.77.1')
    assigned, options = receive(5, 3, b'\x32\x04' + offered + b'\x36\x04' + options[54])
    assert assigned == offered and options[1] == socket.inet_aton('255.255.255.0')
    assert options[3] == socket.inet_aton('192.168.77.1')
    sock.close()
    print(f'Packaged DHCP server assigned {ipaddress.IPv4Address(assigned)} to the virtual USB host; SSH accepted a connection.')
finally:
    for process in processes: process.terminate()
    for process in processes:
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); process.wait()
    for log in logs: log.close()
