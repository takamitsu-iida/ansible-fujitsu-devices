#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
"""fujitsu_srs_facts module.

Gather facts from the node.

Takamitsu IIDA (@takamitsu-iida)
"""

ANSIBLE_METADATA = {'metadata_version': '0.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: fujitsu_srs_facts
short_description: Collect facts from remote devices running Fujitsu SR-S
version_added: 2.9
description:
  - Collects a base set of device facts from a remote device that is running Fujitsu SR-S.
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
    fujitsu_srs_facts:
      gather_subset: default,hardware,interfaces,!config
    when: ansible_network_os == 'fujitsu_srs'

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
# see, module_utils/fujitsu_srs.py
from ansible.module_utils.fujitsu_srs import run_commands, fujitsu_srs_argument_spec, check_args

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

  COMMANDS = ['show system information', 'show running-config sysname']

  """
  AccessFJWAN-SRS# show system information
  --- Fri Jun  8 16:07:30 2018 ---
  Current-time : Fri Jun  8 16:07:30 2018
  Startup-time : Mon Feb  5 10:01:03 2018
  System : SR-S716C2
  Serial No. : 00000105
  ROM Ver. : 1.3
  Firm Ver. : V13.02 NY0019 Fri Mar 26 14:03:40 JST 2010
  Security Software Ver. : SR-S Security Software V01.02
  Startup-config : Fri Sep  1 18:08:39 2017 config1
  Running-config : Mon Feb  5 10:01:03 2018
  MAC : 000b5d891100
  Memory : 256MB
  AccessFJWAN-SRS#
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

    data = self.responses[1]
    if data:
      self.facts['hostname'] = self.parse_hostname(data)

  def parse_firm(self, data):
    """parse firmware version
    """
    # Firm Ver. : V13.02 NY0019 Fri Mar 26 14:03:40 JST 2010
    match = re.search(r'Firm Ver\.(?:\s*):(?:\s*)(?P<target>\S.*)', data)
    if match:
      return match.group('target')

  def parse_version(self, data):
    """parse software version
    """
    # Security Software Ver. : SR-S Security Software V01.02
    match = re.search(r'Security Software Ver\.(?:\s*):(?:\s*)(?P<target>\S.*)', data)
    if match:
      return match.group('target')

  def parse_serialnum(self, data):
    """parse serial number
    """
    # Serial No. : 00000105
    match = re.search(r'Serial No\.(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')

  def parse_model(self, data):
    """parse model info
    """
    # System : SR-S716C2
    match = re.search(r'System(?:\s*):(?:\s*)(?P<target>\S+)', data)
    if match:
      return match.group('target')

  def parse_hostname(self, data):
    """parse hostname
    hostname is not included in the "show system info". so we need "show running-config" output to get hostname infomation.
    show running-config need priviledge escalation.
    """
    #AccessFJWAN-SRS# show run sysname
    #--- Fri Jun  8 18:31:11 2018 ---
    #AccessFJWAN-SRS
    return data.splitlines()[-1]


class Hardware(FactsBase):
  """hardware facts
  """

  COMMANDS = ['show system status']

  """
  AccessFJWAN-SRS# show system status
  --- Fri Jun  8 16:37:49 2018 ---
  Current-time         : Fri Jun  8 16:37:49 2018
  Startup-time         : Mon Feb  5 10:01:03 2018
  restart_cause        : power on
  machine_state        : RUNNING
  power0_state         : NORMAL
  power1_state         : NO_PRESENT
  fan0_state           : NORMAL
  inspiration_state    : NORMAL
  phy_state            : NORMAL
  inspiration_temp     : 51 C
  phy_temp             : 57 C
  AccessFJWAN-SRS#
  """

  def populate(self):
    super(Hardware, self).populate()
    data = self.responses[0]
    if data:
      self.facts['power0_state'] = self.parse_power(0, data)
      self.facts['power1_state'] = self.parse_power(1, data)


  def parse_power(self, power_id, data):
    """parse power state
    """
    prefix = 'power' + str(power_id) + '_state'
    match = re.search(prefix + r'(?:\s*):(?:\s*)(?P<target>\S+)', data)
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
  # show ether
  --- Fri Jun  8 17:48:30 2018 ---
  [ETHER PORT-1]
  status		: auto 1000M Full MDI
  media		: Metal
  flow control	: send off, receive off
  type		: Normal
  since		: Feb  5 10:01:09 2018
  config		: mode(auto), mdi(auto)
  linkcontrol	: online, recovery(-), downrelay(-)

  [ETHER PORT-2]
  status		: auto 1000M Full MDI-X
  media		: Metal
  flow control	: send off, receive off
  type		: Normal
  since		: Feb  5 10:04:35 2018
  config		: mode(auto), mdi(auto)
  linkcontrol	: online, recovery(-), downrelay(-)

  [ETHER PORT-16]
  status		: down
  media		: -
  flow control	: -
  type		: Normal
  since		: Feb  5 10:01:05 2018
  config		: mode(auto), mdi(auto)
  linkcontrol	: online, recovery(-), downrelay(-)

  AccessFJWAN-SRS#


  # show interface
  --- Fri Jun  8 17:50:21 2018 ---
  lan0           MTU 1500    <UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST>
      Type: port vlan
      VLAN ID is 1000
      MAC address: 00:0b:5d:89:11:00
      Status: up since Feb  5 10:04:35 2018
      IP address/masklen:
        192.168.1.200/24       Broadcast 192.168.1.255
      Proxy ARP: enabled
      IPv6 address/prefixlen:
        fe80::20b:5dff:fe89:1100/64
        999::716:1/64
  lo0            MTU 16384   <UP,LOOPBACK,RUNNING,MULTICAST>
      Type: loopback
      Status: up since Feb  5 10:01:05 2018
      IP address/masklen:
        127.0.0.1/32
      IPv6 address/prefixlen:
        fe80::1/64
        ::1/128
  AccessFJWAN-SRS#
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
      # key is "PORT-1"
      # value is "status		: auto 1000M Full MDI"
      intf = dict()
      intf['status'] = self.parse_status(value)
      intf['media'] = self.parse_media(value)
      intf['flowcontrol'] = self.parse_flowcontrol(value)
      intf['type'] = self.parse_type(value)
      intf['since'] = self.parse_since(value)
      intf['config'] = self.parse_config(value)
      intf['linkcontrol'] = self.parse_linkcontrol(value)

      facts[key] = intf

    self.facts['ether_port'] = facts


  def populate_interfaces(self, data):
    for key, value in data.items():
      # key is "lan0"
      # value is "    Type: port vlan"

      # search ipv4 address
      self.facts['interfaces'][key] = dict()
      self.facts['interfaces'][key]['ipv4'] = list()
      match = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}", value)
      if match:
        self.facts['interfaces'][key]['ipv4'].extend(match)
        self.facts['all_ipv4_addresses'].extend(match)

      # search ipv6 address
      self.facts['interfaces'][key]['ipv6'] = list()
      # pylint: disable=C0301
      match = re.findall(r"\s+(\S+:\S+\/\d+)", value)
      if match:
        self.facts['interfaces'][key]['ipv6'].extend(match)
        self.facts['all_ipv6_addresses'].extend(match)


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

      match = re.match(r'^\[ETHER (\S+)\]', line)
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

  def parse_type(self, data):
    match = re.search(r'type(?:\s*):(?:\s*)(?P<target>\S.*)$', data, re.M)
    if match:
      return match.group('target')

  def parse_since(self, data):
    match = re.search(r'since(?:\s*):(?:\s*)(?P<target>\S.*)$', data, re.M)
    if match:
      return match.group('target')

  def parse_config(self, data):
    match = re.search(r'config(?:\s*):(?:\s*)(?P<target>\S.*)$', data, re.M)
    if match:
      return match.group('target')

  def parse_linkcontrol(self, data):
    match = re.search(r'linkcontrol(?:\s*):(?:\s*)(?P<target>\S.*)$', data, re.M)
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

  argument_spec.update(fujitsu_srs_argument_spec)

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
