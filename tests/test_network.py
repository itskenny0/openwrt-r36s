"""Verify USB access services and Wi-Fi client provisioning without radios."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / 'package/system/rk3326-handheld/files'
WORK = ROOT / '.work'


class NetworkTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='test-network-', dir=WORK)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for path in ('bin', 'etc/config', 'etc/init.d', 'usr/libexec', 'usr/sbin', 'sbin', 'var/lock', 'lib'):
            (self.root / path).mkdir(parents=True)
        self.env = dict(os.environ, FIXTURE=str(self.root))
        self.env['PATH'] = str(self.root / 'bin') + os.pathsep + self.env['PATH']
        self.data = {'network.lan.proto': 'static', 'network.lan.ipaddr': '192.168.8.1',
                     'dhcp.lan.interface': 'lan', 'dhcp.lan.limit': '100', 'dhcp.lan.start': '50',
                     'dhcp.lan.ignore': '1', 'dhcp.lan.dhcpv4': 'disabled',
                     'dropbear.main.enable': '0', 'dropbear.main.RootPasswordAuth': 'off',
                     'firewall.wan.name': 'wan', 'firewall.wan.network': 'wan wan6'}
        self.save()
        self.write('bin/uci', '''#!/usr/bin/env python3
import json, os, pathlib, sys
root = pathlib.Path(os.environ['FIXTURE'])
path = root / 'uci.json'
data = json.loads(path.read_text())
args = [x for x in sys.argv[1:] if x != '-q']
if args[0] == 'get':
    if args[1] not in data: sys.exit(1)
    print(data[args[1]])
elif args[0] in ('set', 'add_list'):
    key, value = args[1].split('=', 1)
    if args[0] == 'add_list': value = (data.get(key, '') + ' ' + value).strip()
    data[key] = value
    path.write_text(json.dumps(data))
elif args[0] != 'commit': sys.exit(2)
''')
        self.write('bin/logger', '#!/bin/sh\nexit 0\n')
        self.write('lib/functions.sh', '''
config_load() { :; }
config_foreach() { "$1" wan; }
config_get() { export "$1=$(uci -q get "firewall.$2.$3" || true)"; }
''')
        for command in ('dropbear', 'dnsmasq', 'uhttpd', 'network', 'firewall'):
            self.write('etc/init.d/' + command, '#!/bin/sh\nprintf "%s %s\\n" "${0##*/}" "$*" >> "$FIXTURE/services"\n')
        self.write('sbin/wifi', '#!/bin/sh\nprintf "%s\\n" "$*" >> "$FIXTURE/wifi"\n')
        for name in ('usr/libexec/handheld-usb-access', 'usr/sbin/handheld-wifi'):
            script = (FILES / name).read_text()
            for prefix in ('/etc/', '/lib/', '/var/', '/sbin/'):
                script = script.replace(prefix, str(self.root) + prefix)
            self.write(name, script)

    def write(self, path, text):
        p = self.root / path
        p.write_text(text)
        p.chmod(0o755)

    def save(self):
        (self.root / 'uci.json').write_text(json.dumps(self.data))

    def load(self):
        return json.loads((self.root / 'uci.json').read_text())

    def call(self, helper, *args, stdin=None, expected=0):
        result = subprocess.run(['busybox', 'ash', self.root / helper, *args], input=stdin,
                                env=self.env, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def test_usb_enables_ssh_dhcp_and_luci_preserving_addresses_and_authentication(self):
        self.call('usr/libexec/handheld-usb-access')
        data = self.load()
        for key in ('network.lan.ipaddr', 'dhcp.lan.start', 'dhcp.lan.limit', 'dropbear.main.RootPasswordAuth'):
            self.assertEqual(data[key], self.data[key])
        self.assertEqual(data['dhcp.lan.ignore'], '0')
        self.assertEqual(data['dhcp.lan.dhcpv4'], 'server')
        self.assertEqual(data['dropbear.main.enable'], '1')
        self.assertEqual((self.root / 'services').read_text().splitlines(),
                         ['dropbear enable', 'dropbear reload', 'dnsmasq enable', 'dnsmasq reload', 'uhttpd enable', 'uhttpd reload'])

    def test_no_dhcp_pool_or_dynamic_lan_reports_failure(self):
        self.data['network.lan.proto'] = 'dhcp'
        self.save()
        self.call('usr/libexec/handheld-usb-access', expected=1)
        self.assertFalse((self.root / 'services').exists())
        self.data['network.lan.proto'] = 'static'
        self.data['dhcp.lan.limit'] = '0'
        self.save()
        self.call('usr/libexec/handheld-usb-access', expected=1)

    def test_wifi_credentials_before_hotplug_and_station_firewall(self):
        ssid = "A network '$(touch INJECTED)'"
        password = "test ' password ; x"
        result = self.call('usr/sbin/handheld-wifi', 'configure', stdin=ssid + '\n' + password + '\n')
        data = self.load()
        self.assertEqual(data['wireless.handheld.ssid'], ssid)
        self.assertEqual(data['wireless.handheld.key'], password)
        self.assertEqual(data['wireless.handheld.mode'], 'sta')
        self.assertEqual(data['wireless.handheld.network'], 'wwan')
        self.assertEqual(data['network.wwan.proto'], 'dhcp')
        self.assertEqual(data['firewall.wan.network'], 'wan wan6 wwan')
        self.assertFalse((self.root / 'INJECTED').exists())
        self.assertNotIn(password, result.stdout + result.stderr)
        self.assertFalse((self.root / 'wifi').exists(), 'Tried to enable an absent radio')
        self.assertEqual((self.root / 'etc/config/wireless').stat().st_mode & 0o777, 0o600)
        self.data = data
        self.data.update({'wireless.radio0': 'wifi-device', 'wireless.radio0.disabled': '1',
                          'wireless.default_radio0.disabled': '1'})
        self.save()
        self.call('usr/sbin/handheld-wifi', 'apply')
        self.assertEqual((self.root / 'wifi').read_text().strip(), 'up radio0')
        self.assertEqual(self.load()['wireless.radio0.disabled'], '0')
        self.assertEqual(self.load()['wireless.default_radio0.disabled'], '1')
        self.call('usr/sbin/handheld-wifi', 'configure', stdin=ssid + '\n' + password + '\n')
        self.assertEqual(self.load()['firewall.wan.network'], 'wan wan6 wwan')

    def test_invalid_wifi_credentials_do_not_modify_configuration(self):
        for content in ('\npassword\n', 'x' * 33 + '\npassword\n', 'ssid\nshort\n'):
            self.call('usr/sbin/handheld-wifi', 'configure', stdin=content, expected=2)
            self.assertEqual(self.load(), self.data)
