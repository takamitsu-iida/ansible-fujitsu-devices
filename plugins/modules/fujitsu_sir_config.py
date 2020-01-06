#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
""" fujitsu_sir_config module

Send configuration command to the remote node.

まだ完成してない。

Takamitsu IIDA (@takamitsu-iida)
"""

ANSIBLE_METADATA = {'metadata_version': '0.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = """
---
module: fujitsu_sir_config
version_added: "2.9"
author: "Takamitsu IIDA (@takamitsu-iida)"
short_description: Run config commands on remote devices running Fujitsu Si-R
description:
  - Sends arbitrary config commands to Si-R node.
options:
  lines:
    description:
      - The ordered set of commands that should be sent to the remote device.
    aliases: ['commands']

"""

EXAMPLES = r"""
"""

RETURN = """
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list

updates:
  description: The set of commands sent to the remote device
  returned: when commands was sent
  type: list
"""

# pylint: disable=no-name-in-module
# see, module_util/fujitsu_sir.py
from ansible.module_utils.fujitsu_sir import edit_config

from ansible.module_utils.basic import AnsibleModule


def main():
  """main entry point for module execution
  """

  argument_spec = dict(
    lines=dict(type='list', aliases=['commands'], required=True),
  )

  module = AnsibleModule(
    argument_spec=argument_spec,
    supports_check_mode=True
  )

  lines = module.params['lines']

  result = {
    'changed': False
  }

  if lines and not module.check_mode:
    r = edit_config(module, lines)

    result['changed'] = True
    result['commands'] = lines
    result['updates'] = lines
    result['result'] = r

    # "<ERROR> Need to do reset after execute the save command."
    # これが戻ってきたときに、警告を出す
    commit_resp = r.get('commit_response')
    if commit_resp:
      result['warnings'] = commit_resp

  module.exit_json(**result)


if __name__ == '__main__':
  main()
