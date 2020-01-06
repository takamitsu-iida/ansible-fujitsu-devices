#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
"""fujitsu_ipcom_facts module.

Gather facts from ipcom device.

Takamitsu IIDA (@takamitsu-iida)
"""

ANSIBLE_METADATA = {'metadata_version': '0.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: fujitsu_ipcom_facts
short_description: Collect facts from remote devices running Fujitsu IPCOM
version_added: 2.9
description:
  - Collects a base set of device facts from a remote device that is running Fujitsu IPCOM.
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
    fujitsu_ipcom_facts:
      gather_subset: default,hardware,interfaces,!config
    when: ansible_network_os == 'fujitsu_ipcom'

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
from ansible.module_utils.fujitsu_ipcom import run_commands, fujitsu_ipcom_argument_spec, check_args

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
  """Gather default facts
  """

  COMMANDS = ['show system information']

  """
  ipcom# show system info
  System information

  Current-time:   2019/03/20(Wed)20:49:40
  Startup-time:   2019/03/19(Tue)16:14:26
  System:         IPCOM VE2-100_LS_PLUS
  Device ID:      00VE2100LSP###NB751022XX##BG990001200172
  Software ID:    00VE2100LSP###NB751022XX##BG990001200172
  Firm Ver.:      V01L04 NF0001 B14  Tue, 29 Jan 2019 20:15:49 +0900
  Security Ver.:  V4.2.00
  Startup-config: 2019/03/19(Tue)16:52:42
  Running-config: 2019/03/19(Tue)16:52:42
  CPU Load:
  5seconds:      0%
  1minutes:      0%
  5minutes:      0%
  Memory usage:   41% (1.60GB/3.86GB)
  Connections:    0% (1/100000)
  Process:        139
  ipcom#
  """

  def populate(self):
    # run_commands()
    super(Default, self).populate()

    data = self.responses[0]
    if not data:
      return

    value = self.parse_firm(data)
    if value is not None:
      self.facts['firm'] = value

    value = self.parse_security(data)
    if value is not None:
      self.facts['security'] = value

    value = self.parse_deviceid(data)
    if value is not None:
      self.facts['deviceid'] = value

    value = self.parse_softwareid(data)
    if value is not None:
      self.facts['softwareid'] = value

    value = self.parse_system(data)
    if value is not None:
      self.facts['system'] = value


  def parse_firm(self, data):
    """parse firmware version
    """
    # Firm Ver.:      V01L04 NF0001 B14  Tue, 29 Jan 2019 20:15:49 +0900
    match = re.search(r'Firm Ver\.(?:\s*):(?:\s*)(?P<target>\S.*)', data)
    if match:
      return match.group('target')


  def parse_security(self, data):
    """parse security software version
    """
    # Security Ver.:  V4.2.00
    match = re.search(r'Security Ver\.(?:\s*):(?:\s*)(?P<target>\S.*)', data)
    if match:
      return match.group('target')


  def parse_deviceid(self, data):
    """parse device id
    """
    # Device ID:      00VE2100LSP###NB751022XX##BG990001200172
    match = re.search(r'Device ID(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_softwareid(self, data):
    """parse software id
    """
    # Software ID:    00VE2100LSP###NB751022XX##BG990001200172
    match = re.search(r'Software ID(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_system(self, data):
    """parse system
    """
    # System:         IPCOM VE2-100_LS_PLUS
    match = re.search(r'System(?:\s*):(?:\s*)(?P<target>\S.*)', data)
    if match:
      return match.group('target')


class Hardware(FactsBase):
  """Gather hardware facts
  """

  COMMANDS = ['show system status']

  """
  IPCOM VE2
  ipcom# show system status
  System status

  Current-time: 2019/03/20(Wed)20:50:20
  Hardware Option Status
  HDD: PRESENT

  IPCOM EX2-1100
  ipcom# show system status System status
  Current-time: 2017/07/05(Wed)08:21:56 Fan status: LOW
  Intake status:NORMAL
  Exhaust status:NORMAL
  Cpu0 status:NORMAL Fan Speed(RPM) Fan0 :7848
  Fan1 :7848
  Fan2 :7848 Temperature(deg) Intake :28C
  Exhaust :33C
  Cpu0 :44C
  Power Consumption(W)
  Current :100W
  Maximum :200W
  Hardware Information
  PSU0 Status:NORMAL
  Memory:4096MB
  Hardware Option Status
  HDD: PRESENT
  Slot1:NO_PRESENT
  ipcom#
  """

  def populate(self):
    super(Hardware, self).populate()
    data = self.responses[0]
    if not data:
      return

    value = self.parse_intake(data)
    if value is not None:
      self.facts['intake'] = value

    value = self.parse_exhaust(data)
    if value is not None:
      self.facts['exhaust'] = value

    value = self.parse_fan1(data)
    if value is not None:
      self.facts['fan1'] = value

    value = self.parse_memory(data)
    if value is not None:
      self.facts['memory'] = value

    value = self.parse_hdd(data)
    if value is not None:
      self.facts['hdd'] = value


  def parse_intake(self, data):
    """parse Intake status
    """
    match = re.search(r'Intake status(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_exhaust(self, data):
    """parse Exhaust status
    """
    match = re.search(r'Exhaust status(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_fan1(self, data):
    """parse fan1
    """
    match = re.search(r'Fan1(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_fan2(self, data):
    """parse fan2
    """
    match = re.search(r'Fan2(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_memory(self, data):
    """parse memory
    """
    match = re.search(r'Memory(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


  def parse_hdd(self, data):
    """parse hdd
    """
    #   HDD: PRESENT
    match = re.search(r'HDD(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')


class Config(FactsBase):
  """Gather configuration facts
  """

  COMMANDS = ['show running-config']

  def populate(self):
    super(Config, self).populate()
    data = self.responses[0]
    if data:
      self.facts['config'] = data


class Interfaces(FactsBase):
  """Gather interfaces facts
  """

  COMMANDS = ['show interface']

  """
  IPCOM VE2
  ipcom# show interface
  lan0.0     MTU:   1500  <LINKUP>
    Type: 10gigabit ethernet
    Description:
    MAC address: 00:50:56:83:1a:0d
    IP address: 172.18.0.15/16     Broadcast address: 172.18.255.255
    IP routing: enable
    Proxy ARP: disabled
    IPv6 address: none
    IPv6 routing: disable
  ipcom#

  IPCOM EX2
  ipcom# show interface
  lan0.0 MTU:1500 <LINKUP>
    Type: fast ethernet
    Description: phy-lan0.0
    MAC address: 00:e0:00:00:d8:21
    IP address: 155.1.1.1/24 Broadcast address: 155.1.1.255 IP routing: disable
    Proxy ARP: disabled
    IPv6 address: fe80::1/64
    IPv6 address: 2001:db8:1::1/64
    IPv6 address: 2001:db8:2::1/64 tentative
    IPv6 address: 2001:db8:3::1/64 duplicated
    IPv6 routing: disable
    MTU:1500 <LINKDOWN>
  lan0.1
    Type: ethernet
    Description: lan-bnd1
    Redundant: bnd1: lan0.1, lan1.1
    Proxy ARP: disabled
  """

  def populate(self):
    super(Interfaces, self).populate()

    self.facts['interfaces'] = dict()
    self.facts['all_ipv4_addresses'] = list()
    self.facts['all_ipv6_addresses'] = list()

    data = self.responses[0]
    if not data:
      return

    data = self.parse_interface(data)
    self.populate_interface(data)


  def parse_interface(self, data):
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


  def populate_interface(self, data):
    for key, value in data.items():
      self.facts['interfaces'][key] = dict()

      # IPv4アドレスをすべて見つける
      self.facts['interfaces'][key]['ipv4'] = list()
      # IP address: 172.18.0.15/16     Broadcast address: 172.18.255.255
      match = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}", value)
      if match:
        self.facts['interfaces'][key]['ipv4'].extend(match)
        self.facts['all_ipv4_addresses'].extend(match)

      # IPv6アドレスをすべて見つける
      self.facts['interfaces'][key]['ipv6'] = list()
      # IPv6 address: fe80::1/64
      match = re.findall(r"IPv6 address(?:\s*):(?:\s*)(\S.*)", value)
      if match:
        self.facts['interfaces'][key]['ipv6'].extend(match)
        self.facts['all_ipv6_addresses'].extend(match)

      # Proxy ARP: disabled
      match = re.search(r"Proxy ARP(?:\s*):(?:\s*)(?P<target>\S+)", value)
      if match:
        self.facts['interfaces'][key]['proxy_arp'] = match.group('target')

      # Description:
      match = re.search(r"Description(?:\s*):(?:\s*)(?P<target>\S+)", value)
      if match:
        self.facts['interfaces'][key]['description'] = match.group('target')

      # MAC address: 00:50:56:83:1a:0d
      match = re.search(r"MAC address(?:\s*):(?:\s*)(?P<target>\S+)", value)
      if match:
        self.facts['interfaces'][key]['mac'] = match.group('target')


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

  argument_spec.update(fujitsu_ipcom_argument_spec)

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
