#
# ovirt-setup-lib -- ovirt setup library
# Copyright (C) 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# TODO:
#   - load fixtures from files instead of static strings?
#   - test all the methods
#   - test for errors


from io import StringIO

import commons
from ovirt_setup_lib.hostname import Hostname


class HostnameTestCase(commons.BaseTestCase):

    def setUp(self):
        self.mock_otopi()
        self.apply_patch()
        self.Plugin.command.enum.return_value = ['dig', 'ip']
        self.hostname = Hostname(self.Plugin)

    def test_getLocalAddresses(self):
        self.hostname.command.get.return_value = '/bin/ip'
        self.hostname.execute.return_value = (
            0,
            StringIO(u'''\
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group \
default
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: enp0s25: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast \
state UP group default qlen 1000
    link/ether ae:ee:75:5c:6d:cc brd ff:ff:ff:ff:ff:ff
    inet 10.10.10.10/23 brd 10.10.10.255 scope global dynamic enp0s25
       valid_lft 77485sec preferred_lft 77485sec
    inet6 2620:52:0:2282:56ee:75ff:aaaa:6daa/64 scope global noprefixroute \
dynamic
       valid_lft 2591873sec preferred_lft 604673sec
    inet6 fe80::56ee:75ff:fe5c:6daa/64 scope link
       valid_lft forever preferred_lft forever'''),
            StringIO(u''),
        )

        addr = self.hostname.getLocalAddresses()

        self.assertEqual(addr, set(['10.10.10.10', '127.0.0.1']))

        self.hostname.command.get.assert_called_once_with('ip')
        self.hostname.execute.assert_called_once_with(
            args=('/bin/ip', 'addr'),
        )

    def test_getLocalAddresses_exclude_loopback(self):
        self.hostname.command.get.return_value = '/bin/ip'
        self.hostname.execute.return_value = (
            0,
            StringIO(u'''\
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group \
default
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: enp0s25: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast \
state UP group default qlen 1000
    link/ether ae:ee:75:5c:6d:cc brd ff:ff:ff:ff:ff:ff
    inet 10.10.10.10/23 brd 10.10.10.255 scope global dynamic enp0s25
       valid_lft 77485sec preferred_lft 77485sec
    inet6 2620:52:0:2282:56ee:75ff:aaaa:6daa/64 scope global noprefixroute \
dynamic
       valid_lft 2591873sec preferred_lft 604673sec
    inet6 fe80::56ee:75ff:fe5c:6daa/64 scope link
       valid_lft forever preferred_lft forever'''),
            StringIO(u''),
        )

        addr = self.hostname.getLocalAddresses(exclude_loopback=True)

        self.assertEqual(addr, set(['10.10.10.10']))

        self.hostname.command.get.assert_called_once_with('ip')
        self.hostname.execute.assert_called_once_with(
            args=('/bin/ip', 'addr'),
        )

    def test_getLocalAddresses_exclude_loopback_device(self):
        # Cover https://bugzilla.redhat.com/show_bug.cgi?id=1452243#c2
        self.hostname.command.get.return_value = '/bin/ip'
        self.hostname.execute.return_value = (
            0,
            StringIO(u'''\
5: my-bond: <BROADCAST,MULTICAST,MASTER,UP,LOWER_UP> mtu 1500 qdisc noqueue \
state UP qlen 1000
    link/ether 00:14:5e:dd:05:55 brd ff:ff:ff:ff:ff:ff
    inet 10.35.72.13/24 brd 10.35.72.255 scope global dynamic my-bond
       valid_lft 42000sec preferred_lft 42000sec
    inet6 2620:52:0:2348:6248:5124:671d:1146/64 scope global noprefixroute \
dynamic
       valid_lft 2591821sec preferred_lft 604621sec
    inet6 fe80::b925:96f4:3a25:af8/64 scope link
       valid_lft forever preferred_lft forever'''),
            StringIO(u''),
        )

        addr = self.hostname.getLocalAddresses(
            exclude_loopback=True,
            device="my-bond"
        )

        self.assertEqual(addr, set(['10.35.72.13']))

        self.hostname.command.get.assert_called_once_with('ip')
        self.hostname.execute.assert_called_once_with(
            args=('/bin/ip', 'addr', 'show', 'my-bond'),
        )

    def test_dig_reverse_lookup(self):
        self.hostname.command.get.return_value = '/usr/bin/dig'
        self.hostname.execute.return_value = (
            0,
            StringIO(u'''
; <<>> DiG 9.10.2-P4 <<>> -x 8.8.8.8
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 10489
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;8.8.8.8.in-addr.arpa.          IN      PTR

;; ANSWER SECTION:
8.8.8.8.in-addr.arpa.   28372   IN      PTR     google-public-dns-a.google.com.

;; Query time: 62 msec
;; SERVER: 10.38.5.26#53(10.38.5.26)
;; WHEN: Fri Dec 18 17:07:13 CET 2015
;; MSG SIZE  rcvd: 93

'''),
            StringIO(u''),
        )

        names = self.hostname._dig_reverse_lookup('8.8.8.8')

        self.assertEqual(names, set(['google-public-dns-a.google.com']))

        self.hostname.command.get.assert_called_once_with('dig')
        self.hostname.execute.assert_called_once_with(
            args=['/usr/bin/dig', '-x', '8.8.8.8'],
            raiseOnError=False,
        )

    def test_isResolvedByDNS(self):
        self.hostname.command.get.return_value = '/usr/bin/dig'
        self.hostname.execute.return_value = (
            0,
            StringIO(u'''

; <<>> DiG 9.10.2-P4 <<>> ovirt.org
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 25070
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;ovirt.org.                     IN      A

;; ANSWER SECTION:
ovirt.org.              3600    IN      A       173.255.252.138

;; Query time: 172 msec
;; SERVER: 10.38.5.26#53(10.38.5.26)
;; WHEN: Mon Dec 21 16:15:18 CET 2015
;; MSG SIZE  rcvd: 54

'''),
            StringIO(u''),
        )

        resolved = self.hostname.isResolvedByDNS('ovirt.org')

        self.assertTrue(resolved)

        self.hostname.command.get.assert_called_once_with('dig')
        self.hostname.execute.assert_called_once_with(
            args=['/usr/bin/dig', 'ovirt.org'],
            raiseOnError=False,
        )
