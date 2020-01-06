#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
"""fujitsu_sir_command module.

send commands to remote node and return response.

Takamitsu IIDA (@takamitsu-iida)
"""

ANSIBLE_METADATA = {'metadata_version': '0.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: fujitsu_sir_command
short_description: Run commands on remote devices running Fujitsu Si-R
version_added: 2.9
description:
  - Sends arbitrary commands to an fujitsu si-r router.
options:
  commands:
    description:
      - List of commands to send to the remote device.
    required: True

author:
  - Takamitsu IIDA (@takamitsu-iida)
'''

EXAMPLES = '''
tasks:
  - name: send commands to si-r router
    fujitsu_sir_command:
      commands:
        - show system info
        - show running-config
        - show interface
    register: output
'''

RETURN = '''
stdout:
  description: The set of responses from the commands
  type: list
  returned: always
  sample: [ '...', '...' ]

stdout_lines:
  description: The value of stdout split into a list
  type: list
  returned: always
  sample: [ ['...', '...'], ['...'], ['...'] ]
'''


import time

# pylint: disable=no-name-in-module
# module_utils/fujitsu_sir.py
from ansible.module_utils.fujitsu_sir import run_commands, fujitsu_sir_argument_spec, check_args

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types


def to_lines(stdout):
  """split text to lines and yield it
  """
  for item in stdout:
    if isinstance(item, string_types):
      item = str(item).split('\n')
    yield item


def parse_commands(module, warnings):
  """parse commands
  see Entity class document of module_utils/network/common/utils.py
  """
  transform = ComplexList(dict(command=dict(key=True), prompt=dict(), answer=dict()), module)

  # commands as dict
  commands = transform(module.params['commands'])

  # check_mode restrict command except 'show'
  if module.check_mode:
    for item in list(commands):
      if not item['command'].startswith('show'):
        warnings.append('only show commands are supported when using check mode, not executing `%s`' % item['command'])
        commands.remove(item)

  return commands


def main():
  """main entry point for module execution
  """

  argument_spec = dict(
    commands=dict(type='list', required=True),
    wait_for=dict(type='list', aliases=['waitfor']),
    match=dict(default='all', choices=['all', 'any']),
    retries=dict(default=10, type='int'),
    interval=dict(default=1, type='int')
  )

  argument_spec.update(fujitsu_sir_argument_spec)

  module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

  warnings = list()

  commands = parse_commands(module, warnings)

  result = {
    'changed': False
  }

  check_args(module, warnings)
  result['warnings'] = warnings

  wait_for = module.params['wait_for'] or list()
  conditionals = [Conditional(c) for c in wait_for]

  retries = module.params['retries']
  interval = module.params['interval']
  match = module.params['match']

  while retries > 0:

    responses = run_commands(module, commands)

    for item in list(conditionals):
      if item(responses):
        if match == 'any':
          conditionals = list()
          break
        conditionals.remove(item)

    if not conditionals:
      break

    time.sleep(interval)
    retries -= 1

  if conditionals:
    failed_conditions = [item.raw for item in conditionals]
    msg = 'One or more conditional statements have not been satisfied'
    module.fail_json(msg=msg, failed_conditions=failed_conditions)

  result.update({'changed': False, 'stdout': responses, 'stdout_lines': list(to_lines(responses))})

  module.exit_json(**result)


if __name__ == '__main__':
  main()
