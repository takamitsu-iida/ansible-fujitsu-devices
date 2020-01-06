#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
""" fujitsu_sir_facts module.

Gather facts from remote node.

Takamitsu IIDA (@takamitsu-iida)
"""

ANSIBLE_METADATA = {'metadata_version': '0.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: fujitsu_sir_facts
short_description: Collect facts from remote devices running Fujitsu Si-R
version_added: 2.9
description:
  - Collects a base set of device facts from a remote device that is running Fujitsu Si-R.
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected to a given subset.
    required: false
    default: '!config'

author:
  - Takamitsu IIDA (@takamitsu-iida)
'''

EXAMPLES = '''
  - name: gather facts
    fujitsu_sir_facts:
      gather_subset: default,hardware,interfaces,!config
    when: ansible_network_os == 'fujitsu_sir'

  - debug: var=hostvars[inventory_hostname].ansible_facts
'''

RETURN = """
# default
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: string

ansible_net_serialnum:
  description: The serial number of the remote device
  returned: always
  type: string

ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: string

ansible_net_firm:
  description: The operating system firmware running on the remote device
  returned: always
  type: string

# hardware
ansible_net_power0_state:
  description: The status of power module slot0
  returned: when hardware is configured
  type: string

ansible_net_power1_state:
  description: The status of power module slot1
  returned: when hardware is configured
  type: string

# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is configured
  type: string

# interfaces
ansible_net_all_ipv4_addresses:
  description: All IPv4 addresses configured on the device
  returned: when interfaces is configured
  type: list

ansible_net_all_ipv6_addresses:
  description: All IPv6 addresses configured on the device
  returned: when interfaces is configured
  type: list

ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict

ansible_net_ether_port:
  description: A hash of all ether port running on the system
  returned: when interfaces is configured
  type: dict
"""

import re

# pylint: disable=no-name-in-module
# module_utils/fujitsu_sir.py
from ansible.module_utils.fujitsu_sir import run_commands, fujitsu_sir_argument_spec, check_args

# ansible
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


class FactsBase(object):
  """base class to store device facts
  """

  COMMANDS = list()

  def __init__(self, module):
    self.module = module
    self.facts = dict()
    self.responses = None

  def populate(self):
    self.responses = run_commands(self.module, commands=self.COMMANDS, check_rc=False)

  def run(self, cmd):
    return run_commands(self.module, commands=cmd, check_rc=False)


class Default(FactsBase):
  """default facts
  """

  COMMANDS = ['show system information']

  """
  Si-R220C# show system info
  Current-time : Thu Jan  1 10:59:30 1970
  Startup-time : Thu Jan  1 09:00:00 1970
  System : Si-R220C
  Serial No. : 00002982
  ROM Ver. : 1.2
  Firm Ver. : V35.03 NY0028 Wed Feb  1 16:57:33 JST 2012
  Security Software Ver. : Si-R Security Software V03.03
  Startup-config : Thu Jan  1 10:12:13 1970 config1
  Running-config : Thu Jan  1 10:12:16 1970
  MAC : 0017424a1e8c-0017424a1e8f
  Memory : 128MB
  Si-R220C#
  """

  def populate(self):
    # run_commands()
    super(Default, self).populate()

    data = self.responses[0]
    if data:
      self.facts['firm'] = self.parse_firm(data)
      self.facts['version'] = self.parse_version(data)
      self.facts['serialnum'] = self.parse_serialnum(data)
      self.facts['model'] = self.parse_model(data)


  def parse_firm(self, data):
    """parse firmware version
    """
    # Firm Ver. : V35.03 NY0028 Wed Feb  1 16:57:33 JST 2012
    match = re.search(r'Firm Ver\.(?:\s*):(?:\s*)(?P<target>\S.*)', data)
    if match:
      return match.group('target')


  def parse_version(self, data):
    """parse software version
    """
    # Security Software Ver. : Si-R Security Software V03.03
    match = re.search(r'Security Software Ver\.(?:\s*):(?:\s*)(?P<target>\S.*)', data)
    if match:
      return match.group('target')


  def parse_serialnum(self, data):
    """parse serial number
    """
    # Serial No. : 00002982
    match = re.search(r'Serial No\.(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_model(self, data):
    """parse model info
    """
    # System : Si-R220C
    match = re.search(r'System(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


class Hardware(FactsBase):
  """hardware facts
  """

  COMMANDS = ['show system status']

  """
Si-R220C# show system status
Current-time         : Thu Jan  1 11:02:22 1970
Startup-time         : Thu Jan  1 09:00:00 1970
restart_cause        : power on
machine_state        : RUNNING
inspiration_state    : NORMAL
inspiration_temp     : 51 C
Si-R220C#
  """

  def populate(self):
    super(Hardware, self).populate()
    data = self.responses[0]
    if data:
      self.facts['restart_cause'] = self.parse_restart_cause(data)
      self.facts['machine_state'] = self.parse_machine_state(data)
      self.facts['inspiration_state'] = self.parse_inspiration_state(data)
      self.facts['inspiration_temp'] = self.parse_inspiration_temp(data)


  def parse_restart_cause(self, data):
    """parse restart_cause
    """
    match = re.search(r'restart_cause(?:\s*):(?:\s*)(?P<target>\S.*)', data)
    if match:
      return match.group('target')


  def parse_machine_state(self, data):
    """parse machine state
    """
    match = re.search(r'machine?state(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_inspiration_state(self, data):
    """parse inspiration_state
    """
    match = re.search(r'inspiration_state(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_inspiration_temp(self, data):
    """parse inspiration_temp
    """
    match = re.search(r'inspiration_temp(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


class Config(FactsBase):
  """configuration facts
  """

  COMMANDS = ['show running-config']

  def populate(self):
    super(Config, self).populate()
    data = self.responses[0]
    if data:
      self.facts['config'] = data


class Interfaces(FactsBase):
  """interfaces facts
  """

  COMMANDS = ['show ether', 'show interface']

  """
Si-R220C# show ether
[LAN PORT-0]
status                  : auto 100M Full MDI-X
media                   : Metal
flow control            : send off, receive off
since                   : Jan  1 09:01:39 1970

[LAN PORT-1]
status                  : disable
media                   : -
flow control            : -
since                   : -

[LAN PORT-2]
status                  : disable
media                   : -
flow control            : -
since                   : -

[LAN PORT-3]
status                  : disable
media                   : -
flow control            : -
since                   : -

Si-R220C# show interface
lan0           MTU 1500    <UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST>
    Type: ethernet
    MAC address: 00:17:42:4a:1e:8c
    Status: up since Jan  1 09:01:39 1970
    IP address/masklen:
      172.20.0.200/24       Broadcast 172.20.0.255
    ICMP redirect: enabled
    Proxy ARP: enabled
lo0            MTU 16384   <UP,LOOPBACK,RUNNING,MULTICAST>
    Type: loopback
    Status: up since Jan  1 09:00:04 1970
    IP address/masklen:
      127.0.0.1/32
    IPv6 address/prefixlen:
      fe80::1/64
      ::1/128
Si-R220C#
  """

  def populate(self):
    super(Interfaces, self).populate()

    self.facts['interfaces'] = dict()
    self.facts['all_ipv4_addresses'] = list()
    self.facts['all_ipv6_addresses'] = list()

    # ether_port
    data = self.responses[0]
    if data:
      data = self.parse_ether_port(data)
      self.populate_ether_port(data)

    # interfaces
    data = self.responses[1]
    if data:
      data = self.parse_interfaces(data)
      self.populate_interfaces(data)


  def populate_ether_port(self, ports):
    facts = dict()
    for key, value in iteritems(ports):
      intf = dict()
      intf['status'] = self.parse_status(value)
      intf['media'] = self.parse_media(value)
      intf['flowcontrol'] = self.parse_flowcontrol(value)
      intf['since'] = self.parse_since(value)

      facts[key] = intf

    self.facts['lan_port'] = facts


  def populate_interfaces(self, data):
    for key, value in data.items():
      self.facts['interfaces'][key] = dict()
      self.facts['interfaces'][key]['ipv4'] = list()
      match = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}", value)
      if match:
        self.facts['interfaces'][key]['ipv4'].extend(match)
        self.facts['all_ipv4_addresses'].extend(match)
      match = re.search(r"Proxy ARP(?:\s*):(?:\s*)(?P<target>\S+)", value)
      if match:
        self.facts['interfaces'][key]['proxy_arp'] = match.group('target')
      match = re.search(r"ICMP redirect(?:\s*):(?:\s*)(?P<target>\S+)", value)
      if match:
        self.facts['interfaces'][key]['icmp_redirect'] = match.group('target')


  def parse_ether_port(self, data):
    """parse show ether
    """
    parsed = dict()
    key = ''
    for line in data.split('\n'):
      if not line:
        # blank line
        continue
      if line.startswith('---'):
        # command timestamp
        continue

      match = re.match(r'^\[LAN (PORT-\d+)\]', line)
      if match:
        key = match.group(1)
        parsed[key] = line
        continue

      if ': ' in line:
        parsed[key] += '\n%s' % line

    return parsed


  def parse_status(self, data):
    match = re.search(r'status(?:\s*):(?:\s*)(?P<target>\S.*)$', data, re.M)
    if match:
      return match.group('target')

  def parse_media(self, data):
    match = re.search(r'media(?:\s*):(?:\s*)(?P<target>\S.*)$', data, re.M)
    if match:
      return match.group('target')

  def parse_flowcontrol(self, data):
    match = re.search(r'flow control(?:\s*):(?:\s*)(?P<target>\S.*)$', data, re.M)
    if match:
      return match.group('target')

  def parse_since(self, data):
    match = re.search(r'since(?:\s*):(?:\s*)(?P<target>\S.*)$', data, re.M)
    if match:
      return match.group('target')



  def parse_interfaces(self, data):
    parsed = dict()
    key = ''
    for line in data.split('\n'):
      if not line:
        # blank line
        continue
      if line.startswith('---'):
        # command timestamp
        continue

      if line.startswith(' '):
        parsed[key] += '\n%s' % line
      else:
        match = re.match(r'^(\S+)\s+MTU', line)
        if match:
          key = match.group(1)
          parsed[key] = line
    return parsed


FACT_SUBSETS = dict(
  default=Default,
  hardware=Hardware,
  interfaces=Interfaces,
  config=Config
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
  """main entry point for module execution
  """

  argument_spec = dict(gather_subset=dict(default=['!config'], type='list'))

  argument_spec.update(fujitsu_sir_argument_spec)

  module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

  gather_subset = module.params['gather_subset']

  runable_subsets = set()
  exclude_subsets = set()

  for subset in gather_subset:
    if subset == 'all':
      runable_subsets.update(VALID_SUBSETS)
      continue

    if subset.startswith('!'):
      subset = subset[1:]
      if subset == 'all':
        exclude_subsets.update(VALID_SUBSETS)
        continue
      exclude = True
    else:
      exclude = False

    if subset not in VALID_SUBSETS:
      module.fail_json(msg='Bad subset')

    if exclude:
      exclude_subsets.add(subset)
    else:
      runable_subsets.add(subset)

  if not runable_subsets:
    runable_subsets.update(VALID_SUBSETS)

  runable_subsets.difference_update(exclude_subsets)
  runable_subsets.add('default')

  facts = dict()
  facts['gather_subset'] = list(runable_subsets)

  instances = list()
  for key in runable_subsets:
    instances.append(FACT_SUBSETS[key](module))

  for inst in instances:
    inst.populate()
    facts.update(inst.facts)

  # prepend 'ansible_net_' to the facts key
  ansible_facts = dict()
  for key, value in iteritems(facts):
    key = 'ansible_net_%s' % key
    ansible_facts[key] = value

  warnings = list()
  check_args(module, warnings)

  module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
  main()
