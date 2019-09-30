#
# ovirt-setup-lib -- ovirt setup library
# Copyright (C) 2013-2016 Red Hat, Inc.
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


import gettext
import netaddr
import re
import six
import socket

from otopi import base, util
from otopi import plugin as oplugin

from ovirt_setup_lib import dialog


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-setup-lib')


@util.export
class Hostname(base.Base):
    _DOMAIN_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            [A-Za-z0-9\.\-]+
            $
        """
    )

    _INTERFACE_RE_STR = r'(?P<interface>\w+([-.]\w+)*(\.\w+)?)'

    _INTERFACE_RE = re.compile(
        pattern=_INTERFACE_RE_STR,
    )

    _IP_INTERFACE_RE = re.compile(
        flags=re.VERBOSE,
        pattern='{pref}{iface}{suff}'.format(
            pref=r"""
                ^
                \d+
                :
                \s+
            """,
            iface=_INTERFACE_RE_STR,
            suff=r"""
                (@\w+)?
                :
                \s+
                <(?P<options>[^>]+)
                .*
            """,
        ),
    )

    _ADDRESS_RE_STR = '(?P<address>[0-9a-fA-F:.]+)'

    _IP_ADDRESS_RE = re.compile(
        flags=re.VERBOSE,
        pattern='{pref}{addr}{suff}'.format(
            pref=r"""
                \s+
                inet6?
                \s
            """,
            addr=_ADDRESS_RE_STR,
            suff=r"""
                /\d{1,3}
                .*
                $
            """,
        ),
    )

    _ADDRESS_SCOPE_RE = re.compile(
        pattern='{addr}%{scope}'.format(
            addr=_ADDRESS_RE_STR,
            scope='(?P<scope>.*)',  # Can't use _INTERFACE_RE_STR
        ),
    )

    _DIG_LOOKUP_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            [\w.-]+
            \s+
            \d+
            \s+
            IN
            \s+
            (A|AAAA|CNAME)
            \s+
            [\w.-]+
        """
    )

    _DIG_REVLOOKUP_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            [\w/.-]+\.in-addr\.arpa\.
            \s+
            \d+
            \s+
            IN
            \s+
            PTR
            \s+
            (?P<answer>[\w/.-]+)
            \.
            $
        """
    )

    _REQUIRED_CMD = set(['dig', 'ip'])

    def __init__(self, plugin):
        super(Hostname, self).__init__()
        self._plugin = plugin

        context = self._plugin.context
        if hasattr(context, 'currentStage'):
            current_stage = context.currentStage
        else:
            msg = _(
                '{classname} cannot be initialized out of '
                'OTOPI stages'
            ).format(
                classname=type(self).__name__,
            )
            self.logger.error(msg)
            raise RuntimeError(msg)

        if current_stage < oplugin.Stages.STAGE_PROGRAMS:
            for cmd in self._REQUIRED_CMD:
                self.command.detect(cmd)
        else:
            self.logger.debug(
                (
                    '{classname} initialized only at stage {current_stage} '
                    'so the detection of the required commands is up to '
                    'the caller object'
                ).format(
                    classname=type(self).__name__,
                    current_stage=current_stage,
                )
            )
        cmd_to_be_detected = set(self.command.enum())
        if not self._REQUIRED_CMD.issubset(cmd_to_be_detected):
            msg = _(
                'Not all of the required commands have been required for '
                'command detection, please instantiate this class '
                'before STAGE_PROGRAMS or externally detect'
            )
            self.logger.error(msg)
            raise RuntimeError(msg)

    @property
    def plugin(self):
        return self._plugin

    @property
    def command(self):
        return self._plugin.command

    @property
    def dialog(self):
        return self._plugin.dialog

    @property
    def execute(self):
        return self._plugin.execute

    @property
    def environment(self):
        return self._plugin.environment

    @property
    def logger(self):
        return self._plugin.logger

    @staticmethod
    def valid_ip_address(address):
        return netaddr.valid_ipv4(address)

    def getLocalAddresses(
        self,
        exclude_loopback=False,
        device=None,
        with_subnet=False
    ):
        interfaces = {}
        addresses = {}
        if device:
            rc, stdout, stderr = self.execute(
                args=(
                    self.command.get('ip'),
                    'addr',
                    'show',
                    device,
                ),
            )
        else:
            rc, stdout, stderr = self.execute(
                args=(
                    self.command.get('ip'),
                    'addr',
                ),
            )
        for line in stdout:
            interfacematch = self._IP_INTERFACE_RE.match(line)
            addressmatch = self._IP_ADDRESS_RE.match(line)
            if interfacematch is not None:
                iface = interfacematch.group('interface')
                interfaces[
                    iface
                ] = 'LOOPBACK' in interfacematch.group('options')
            elif addressmatch is not None:
                addresses.setdefault(
                    iface,
                    []
                ).append(
                    addressmatch.group('address')
                )
        iplist = []
        for interface, loopback in six.iteritems(interfaces):
            if exclude_loopback and loopback:
                pass
            else:
                iplist.extend(addresses.get(interface, []))
        if not with_subnet:
            iplist = [i.split('/')[0] for i in iplist]

        self.logger.debug('addresses: %s' % iplist)
        return set(iplist)

    def _dig_reverse_lookup(self, addr):
        names = set()
        args = [
            self.command.get('dig'),
            '-x',
            addr,
        ]
        rc, stdout, stderr = self.execute(
            args=args,
            raiseOnError=False
        )
        if rc == 0:
            for line in stdout:
                found = self._DIG_REVLOOKUP_RE.search(line)
                if found:
                    names.add(found.group('answer'))
        return names

    def _validateFQDNresolvability(
        self,
        fqdn,
        system,
        dns,
        reverse_dns,
        local_non_loopback,
        not_local,
        not_local_text,
    ):

        if system:
            try:
                resolvedAddresses = self.getResolvedAddresses(fqdn)
                self.logger.debug(
                    '{fqdn} resolves to: {addresses}'.format(
                        fqdn=fqdn,
                        addresses=resolvedAddresses,
                    )
                )
                resolvedAddressesAsString = ' '.join(resolvedAddresses)
            except socket.error:
                raise RuntimeError(
                    _('{fqdn} did not resolve into an IP address').format(
                        fqdn=fqdn,
                    )
                )

        if dns:
            resolvedByDNS = self.isResolvedByDNS(fqdn)
            if not resolvedByDNS:
                self.logger.warning(
                    _(
                        'Failed to resolve {fqdn} using DNS, '
                        'it can be resolved only locally'
                    ).format(
                        fqdn=fqdn,
                    )
                )
            elif reverse_dns:
                revResolved = False
                for address in resolvedAddresses:
                    for name in self._dig_reverse_lookup(address):
                        revResolved = name.lower() == fqdn.lower()
                        if revResolved:
                            break
                    if revResolved:
                        break
                if not revResolved:
                    raise RuntimeError(
                        _(
                            'The following addresses: {addresses} did not '
                            'reverse resolve into {fqdn}'
                        ).format(
                            addresses=resolvedAddressesAsString,
                            fqdn=fqdn
                        )
                    )

        if local_non_loopback:
            if not resolvedAddresses.issubset(
                    self.getLocalAddresses(exclude_loopback=True)
            ):
                raise RuntimeError(
                    _(
                        '{fqdn} resolves to {addresses} and '
                        'not all of them can be mapped '
                        'to non loopback devices on this host'
                    ).format(
                        fqdn=fqdn,
                        addresses=resolvedAddressesAsString
                    )
                )

        if not_local:
            if resolvedAddresses.intersection(
                self.getLocalAddresses(exclude_loopback=False)
            ):
                raise RuntimeError(
                    _(
                        '{fqdn} resolves to {addresses}, and at least one of '
                        'them is locally used on this machine. '
                        '{not_local_text}'
                    ).format(
                        fqdn=fqdn,
                        addresses=resolvedAddressesAsString,
                        not_local_text=not_local_text,
                    )
                )

    def _validateFQDN(self, fqdn):
        if self.valid_ip_address(fqdn):
            raise RuntimeError(
                _(
                    '{fqdn} is an IP address and not a FQDN. '
                    'A FQDN is needed to be able to generate '
                    'certificates correctly.'
                ).format(
                    fqdn=fqdn,
                )
            )

        if not fqdn:
            raise RuntimeError(
                _('Please specify host FQDN')
            )

        if len(fqdn) > 1000:
            raise RuntimeError(
                _('FQDN has invalid length')
            )

        components = fqdn.split('.', 1)
        if len(components) == 1:
            self.logger.warning(
                _('Host name {fqdn} has no domain suffix').format(
                    fqdn=fqdn,
                )
            )
        if not components[0] or not self._DOMAIN_RE.match(fqdn):
            raise RuntimeError(
                _('Host name {fqdn} is not valid').format(
                    fqdn=fqdn,
                )
            )

    def isResolvedByDNS(self, fqdn):
        args = [
            self.command.get('dig'),
            '+noall',
            '+answer',
            fqdn,
            'ANY',
        ]
        rc, stdout, stderr = self.execute(
            args=args,
            raiseOnError=False
        )
        resolved = False
        if rc == 0:
            for line in stdout:
                if self._DIG_LOOKUP_RE.search(line):
                    resolved = True
        return resolved

    def getResolvedAddresses(self, fqdn):
        res = set([])
        for __, __, __, __, sockaddr in socket.getaddrinfo(
            fqdn,
            None,
        ):
            address = sockaddr[0]
            # python's getaddrinfo seems to simply wrap libc's getaddrinfo,
            # which (see getaddrinfo(3) manpage):
            # "supports the address%scope-id notation for specifying the IPv6
            # scope-ID.". See also: https://tools.ietf.org/html/rfc4007
            addr_scope_match = self._ADDRESS_SCOPE_RE.match(address)
            if addr_scope_match:
                address = addr_scope_match.group('address')
            res.add(address)
        self.logger.debug('getResolvedAddresses: %s', res)
        return res

    def getHostnameTester(
        self,
        validate_syntax=False,  # Validate fqdn syntax
        system=True,  # Local resolver
        dns=False,  # dig against default name server(s)
        reverse_dns=True,  # dig -x, check only if dns==True
        local_non_loopback=False,  # matches a local non-loopback address
        not_local=False,  # If True, refuse a name of the current machine
        not_local_text='',  # Additional hint if it fails not_local test
        allow_empty=False,  # Allow empty responses
    ):

        def test_hostname(name):
            res = ''
            try:
                if not (allow_empty and not name):
                    if validate_syntax:
                        self._validateFQDN(name)
                    self._validateFQDNresolvability(
                        name,
                        system,
                        dns,
                        reverse_dns,
                        local_non_loopback,
                        not_local,
                        not_local_text,
                    )
            except RuntimeError as e:
                res = _('Host name is not valid: {e}').format(e=e)
                self.logger.debug('test_hostname exception', exc_info=True)
            return res

        return test_hostname

    def fqdnLocalhostValidation(self, fqdn):
        res = ''
        if fqdn == 'localhost' or fqdn == 'localhost.localdomain':
            res = _("Using the name 'localhost' is not recommended, "
                    "and may cause problems later on.")
        return res

    def getHostname(
        self,
        envkey,
        whichhost,
        supply_default,
        prompttext=None,
        dialog_name=None,
        **tester_kwarg
    ):

        if prompttext is None:
            prompttext = _(
                'Host fully qualified DNS name of {whichhost} server'
            ).format(
                whichhost=whichhost,
            )
        if dialog_name is None:
            dialog_name = 'OVESETUP_NETWORK_FQDN_{whichhost}'.format(
                whichhost=whichhost.replace(' ', '_'),
            )
        return dialog.queryEnvKey(
            name=dialog_name,
            dialog=self.dialog,
            logger=self.logger,
            env=self.environment,
            key=envkey,
            note=_(
                '{prompt} [@DEFAULT@]: '
            ).format(
                prompt=prompttext,
            ),
            prompt=True,
            default=socket.getfqdn() if supply_default else '',
            tests=(
                {
                    'test': self.getHostnameTester(**tester_kwarg),
                },
                {
                    'test': self.fqdnLocalhostValidation,
                    'is_error': False,
                    'warn_note': 'Are you sure?',
                },
            ),
            store=(True if envkey else False),
        )


# vim: expandtab tabstop=4 shiftwidth=4
