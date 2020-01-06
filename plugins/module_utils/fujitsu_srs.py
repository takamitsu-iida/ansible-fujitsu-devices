#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: disable=protected-access
"""module_utils/fujitsu_srs.py

Utility functions for the fujitsu sr-s switch modules.

Takamitsu IIDA (@takamitsu-iida)
"""

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import Connection
from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError

# cache for device configuration
_DEVICE_CONFIGS = {}

fujitsu_srs_provider_spec = {
  'host': dict(),
  'port': dict(type='int'),
  'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
  'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
  'ssh_keyfile': dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
  'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
  'auth_pass': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS']), no_log=True),
  'timeout': dict(type='int')
}

# required argument to create module
fujitsu_srs_argument_spec = {
  'provider': dict(type='dict', options=fujitsu_srs_provider_spec),
}

fujitsu_srs_top_spec = {
  'host': dict(removed_in_version=2.9),
  'port': dict(removed_in_version=2.9, type='int'),
  'username': dict(removed_in_version=2.9),
  'password': dict(removed_in_version=2.9, no_log=True),
  'ssh_keyfile': dict(removed_in_version=2.9, type='path'),
  'authorize': dict(fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
  'auth_pass': dict(removed_in_version=2.9, no_log=True),
  'timeout': dict(removed_in_version=2.9, type='int')
}

fujitsu_srs_argument_spec.update(fujitsu_srs_top_spec)


def get_provider_argspec():
  return fujitsu_srs_provider_spec


def get_connection(module):
  """Retrieves the Connection class object or cache
  """
  if hasattr(module, '_fujitsu_srs_connection'):
    return module._fujitsu_srs_connection

  capabilities = get_capabilities(module)
  network_api = capabilities.get('network_api')
  if network_api == 'cliconf':
    module._fujitsu_srs_connection = Connection(module._socket_path)
  else:
    module.fail_json(msg='Invalid connection type %s' % network_api)

  return module._fujitsu_srs_connection


def get_capabilities(module):
  """Retrieves the capabilities object or cache
  """
  if hasattr(module, '_fujitsu_srs_capabilities'):
    return module._fujitsu_srs_capabilities

  connection = Connection(module._socket_path)

  # see cliconf/fujitsu_srs.py
  capabilities = connection.get_capabilities()

  # cache it
  module._fujitsu_srs_capabilities = json.loads(capabilities)
  return module._fujitsu_srs_capabilities


def check_args(module, warnings):
  """check args.
  """
  # pylint: disable=unnecessary-pass
  # pylint: disable=unused-argument
  pass


def get_config(module, flags=None):
  """Retrieves the current config from the device or cache
  """
  flags = [] if flags is None else flags

  cmd = 'show running-config '
  cmd += ' '.join(flags)
  cmd = cmd.strip()

  try:
    return _DEVICE_CONFIGS[cmd]
  except KeyError:
    connection = get_connection(module)
    # see cliconf/fujitsu_srs.py
    out = connection.get_config(flags=flags)
    cfg = to_text(out, errors='surrogate_then_replace').strip()
    _DEVICE_CONFIGS[cmd] = cfg
    return cfg


def run_commands(module, commands, check_rc=True):
  responses = list()
  connection = get_connection(module)

  for cmd in to_list(commands):
    if isinstance(cmd, dict):
      command = cmd['command']
      prompt = cmd['prompt']
      answer = cmd['answer']
    else:
      command = cmd
      prompt = None
      answer = None

    try:
      # see cliconf/fujitsu_srs.py
      out = connection.get(command, prompt, answer)
    except AnsibleConnectionError as e:
      if check_rc:
        raise
      else:
        out = e

    try:
      out = to_text(out, errors='surrogate_or_strict')
    except UnicodeError:
      module.fail_json(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

    responses.append(out)

  return responses


def edit_config(module, commands):
  """edit config
  """
  connection = get_connection(module)

  # see plugin/cliconf/fujitsu_srs.py
  return connection.edit_config(commands)
