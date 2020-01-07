#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
"""fujitsu_ipcom_config module.

Send configuration commands to the remote node.

Takamitsu IIDA (@takamitsu-iida)
"""

ANSIBLE_METADATA = {'metadata_version': '0.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = """
---
module: fujitsu_ipcom_config
version_added: "2.9"
author: "Takamitsu IIDA (@takamitsu-iida)"
short_description: Run config commands on remote devices running Fujitsu IPCOM
description:
  - Sends arbitrary config commands to IPCOM node.
options:
  lines:
    description:
      - The ordered set of commands that should be sent to the remote device.
    aliases: ['commands']

"""

EXAMPLES = r"""
"""

RETURN = """
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig

# pylint: disable=no-name-in-module
# see, module_utils/fujitsu_ipcom.py and plugins/cliconf/fujitsu_ipcom.py
from ansible.module_utils.fujitsu_ipcom import edit_config, run_commands


def save_config(module, result):
  result['changed'] = True
  if not module.check_mode:
    run_commands(module, 'copy running-config startup-config\r')
  else:
    module.warn('Configuration not saved due to check mode')


def main():
  """main entry point for module execution
  """

  argument_spec = dict(
    lines=dict(type='list', aliases=['commands'], required=True),
    save_when=dict(choices=['always', 'never', 'modified', 'changed'], default='never'),
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

    commit_resp = r.get('commit_response')
    if commit_resp:
      result['warnings'] = commit_resp

  if module.params['save_when'] == 'modified':
    output = run_commands(module, ['show running-config', 'show startup-config'])

    diff_ignore_lines = module.params['diff_ignore_lines']
    running_config = NetworkConfig(indent=1, contents=output[0], ignore_lines=diff_ignore_lines)
    startup_config = NetworkConfig(indent=1, contents=output[1], ignore_lines=diff_ignore_lines)

    if running_config.sha1 != startup_config.sha1:
      save_config(module, result)

  module.exit_json(**result)


if __name__ == '__main__':
  main()
