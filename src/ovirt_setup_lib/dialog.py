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


"""Dialog."""


import gettext

from otopi import util

try:
    import pwquality
    _use_pwquality = True
except ImportError:
    # do not force this optional feature
    _use_pwquality = False


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-setup-lib')


@util.export
def queryBoolean(
    dialog,
    name,
    note,
    prompt,
    true=_('Yes'),
    false=_('No'),
    default=False,
):
    return dialog.queryString(
        name=name,
        note=note,
        prompt=prompt,
        validValues=(true, false),
        caseSensitive=False,
        default=true if default else false,
    ) != false.lower()


@util.export
def queryEnvKey(
    dialog,
    logger,
    env,
    key,
    note,
    tests=None,
    validValues=None,
    caseSensitive=True,
    hidden=False,
    prompt=False,
    default=None,
    name=None,
    store=True,
    max_attemps=1000,
):
    """Query string and validate it.
    Params:
        dialog - plugin.dialog
        logger - plugin.logger
        env - a dict to store result into, usually plugin.environment
        key - key in env to store result into
            if env[key] is set, do not query
        note - prompt to be displayed to the user
        tests - tests to run on the input value

    tests is a list of dicts, each having:
    'test' -- Accepts a value and returns an error message if bad
    'is_error' -- True (default) if a failure is an error, else a warning
        If True and a test failed, ask user again. Otherwise prompt user
        to accept value anyway.
    'warn_note' -- Message displayed if warning
    'warn_name' -- warn dialog name
    'interactive_only' -- Do not run test if env[key] is already set
    'store' -- Store the value in environment
    """

    logger.debug(
        'queryEnvKey called for key {key}'.format(
            key=key,
        )
    )
    interactive = key not in env or env[key] is None
    valid = False
    attemps = 0
    while not valid and attemps < max_attemps:
        if interactive:
            value = dialog.queryString(
                name=(
                    'queryEnvKey_input_{key}'.format(key=key)
                    if name is None
                    else name
                ),
                note=note,
                validValues=validValues,
                caseSensitive=caseSensitive,
                hidden=hidden,
                prompt=prompt,
                default=default,
            )
        else:
            value = env[key]
        valid = True
        for test in tests if tests else ():
            if not interactive and test.get('interactive_only', False):
                continue
            msg = test['test'](value)
            if msg:
                if interactive:
                    if test.get('is_error', True):
                        logger.error(msg)
                        valid = False
                        attemps += 1
                        break
                    else:
                        logger.warning(msg)
                        if not queryBoolean(
                            dialog=dialog,
                            name=(
                                'queryEnvKey_warnverify_{key}'.format(
                                    key=key
                                ) if test.get('warn_name') is None
                                else test['warn_name']
                            ),
                            note='{msg} (@VALUES@) [@DEFAULT@]: '.format(
                                msg=test.get('warn_note', _('OK? ')),
                            ),
                            prompt=True,
                            default=False,
                        ):
                            valid = False
                            attemps += 1
                            break
                else:  # Not interactive
                    if test.get('is_error', True):
                        logger.error(msg)
                        raise RuntimeError(msg)
                    else:
                        logger.warning(msg)
    if attemps == max_attemps:
        raise RuntimeError('Maximum retry count has been reached')
    if store:
        env[key] = value
    return value


@util.export
def queryPassword(
    dialog,
    logger,
    env,
    key,
    note,
    verify_same=True,
    note_verify_same=None,
    error_msg_not_same=None,
    verify_hard=True,
    warn_not_hard=None,
    tests=None,
):
    """Get a password from the user.
    Params:
        dialog - plugin.dialog
        logger - plugin.logger
        env - a dict to store result into, usually plugin.environment
        key - key in env to store result into
            if env[key] is set, do not query, but do run check and
            warn if verify_hard is True and password not hard enough
        note - prompt to be displayed to the user
        verify_same - if true, query user to input password again
            and verify that they are the same
        note_verify_same - prompt to be displayed when querying again
        error_msg_not_same - error message to be displayed if not same
        verify_hard - optionally check that it is hard enough,
            if pwquality is installed
        warn_not_hard - warning to be displayed if not hard enough
            if string includes '{error}', it will be replaced by
            actual error returned from pwquality
        tests - extra tests to run, in the format of queryEnvKey
    """

    def password_hard_enough(password):
        res = ''
        try:
            if(_use_pwquality):
                pwq = pwquality.PWQSettings()
                pwq.read_config()
                pwq.check(password, None, None)
        except pwquality.PWQError as e:
            res = warn_not_hard.format(error=e.args[1])
        return res

    if not note_verify_same:
        note_verify_same = _('Please confirm password: ')
    if not error_msg_not_same:
        error_msg_not_same = _('Passwords do not match')
    if not warn_not_hard:
        warn_not_hard = _('Password is weak: {error}')
    return queryEnvKey(
        dialog=dialog,
        logger=logger,
        env=env,
        key=key,
        note=note,
        prompt=True,
        hidden=True,
        tests=(
            {
                'test': lambda value: (
                    '' if value == queryEnvKey(
                        dialog=dialog,
                        logger=logger,
                        env={},
                        key='second_password',
                        note=note_verify_same,
                        prompt=True,
                        hidden=True,
                    ) else error_msg_not_same
                ),
                'interactive_only': True,
            },
            {
                'test': password_hard_enough,
                'is_error': False,
                'warn_note': 'Use weak password? ',
            },
        ) + (
            tests
            if tests is not None
            else ()
        ),
    )


# vim: expandtab tabstop=4 shiftwidth=4
