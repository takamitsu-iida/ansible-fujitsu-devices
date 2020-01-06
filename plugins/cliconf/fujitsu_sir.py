# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""plugins/cliconf/fujitsu_sir.py

cliconf plugin for fujitsu_sir

Takamitsu IIDA (@takamitsu-iida)
"""

import collections
import json
import re

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
# from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

  # connection.get_capabilities()
  def get_capabilities(self):
    """Retrieves supported capabilities

    CliconfBaseの中でget_capabilities()は最小限以下の情報を返せ、と書かれている。
      {
        'rpc': [list of supported rpcs],
        'network_api': <str>, # the name of the transport
        'device_info': {
          'network_os': <str>,
          'network_os_version': <str>,
          'network_os_model': <str>,
          'network_os_hostname': <str>,
          'network_os_image': <str>,
          'network_os_platform': <str>,
        },
        'device_operations': {
          'supports_replace': <bool>,            # identify if config should be merged or replaced is supported
          'supports_commit': <bool>,             # identify if commit is supported by device or not
          'supports_rollback': <bool>,           # identify if rollback is supported or not
          'supports_defaults': <bool>,           # identify if fetching running config with default is supported
          'supports_commit_comment': <bool>,     # identify if adding comment to commit is supported of not
          'supports_onbox_diff: <bool>,          # identify if on box diff capability is supported or not
          'supports_generate_diff: <bool>,       # identify if diff capability is supported within plugin
          'supports_multiline_delimiter: <bool>, # identify if multiline demiliter is supported within config
          'support_match: <bool>,                # identify if match is supported
          'support_diff_ignore_lines: <bool>,    # identify if ignore line in diff is supported
        }
        'format': [list of supported configuration format],
        'match': ['line', 'strict', 'exact', 'none'],
        'replace': ['line', 'block', 'config'],
      }
    """

    result = dict()

    # CliconfBaseのget_base_rpc()は ['get_config', 'edit_config', 'get_capabilities', 'get'] を返却する。
    # Fujitsu Si-Rはcommitとdiscard_changesをサポートするので、それらを追加する。
    result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes']

    # トランスポートは'cliconf'の一択
    result['network_api'] = 'cliconf'

    # デバイス情報
    result['device_info'] = self.get_device_info()

    # デバイスがサポートするオペレーション
    result['device_operations'] = self.get_device_operations()

    # サポートしているコンフィグのフォーマット
    result['format'] = ['text']

    result['match'] = ['none']

    result['replace'] = ['line']

    return json.dumps(result)


  @enable_mode
  def get_config(self, source='running', flags=None, format='text'):
    # pylint: disable=redefined-builtin
    if source not in ('running', 'startup'):
      raise AnsibleError("fetching configuration from %s is not supported" % source)

    if source == 'running':
      cmd = 'show running-config '
    else:
      cmd = 'show startup-config '

    if flags:
      cmd += ' '.join(to_list(flags))

    cmd = cmd.strip()
    return self.send_command(cmd)


  @enable_mode
  def get_diff(self, candidate=None, running=None, diff_match='line', diff_ignore_lines=None, path=None, diff_replace='line'):
    """
    Generate diff between candidate and running configuration.
    """
    diff = {}
    return json.dumps(diff)


  @enable_mode
  def edit_config(self, candidate, commit=True, replace=None, diff=False, comment=None):
    """send configuration commands

    Keyword Arguments:
      candidate {list} -- configuration commands to be sent (default: {None})
      commit {bool} -- do commit, this must be True (default: {True})
      replace {list} -- not supported yet (default: {None})
      comment {str} -- not supported yet (default: {None})

    Raises:
      ValueError -- raise error when candidate is not provided.

    Returns:
      dict -- { request: [], response: []}
    """
    # pylint: disable=signature-differs

    if not candidate:
      raise ValueError('must provide a candidate config to load')

    if not commit:
      raise ValueError('check mode is not supported')

    # change to configuration mode
    self.send_command('configure')

    requests = []
    responses = []
    for line in to_list(candidate):
      if not isinstance(line, collections.Mapping):
        line = {'command': line}

      cmd = line['command']
      if cmd != 'end' and cmd != 'commit' and cmd != 'discard' and cmd[0] != '#':
        r = self.send_command(**line)
        responses.append(r)
        requests.append(cmd)

    commit_responses = []
    r = self.send_command('commit')
    if r:
      commit_responses.append(r)

    r = self.send_command('save')
    if r:
      commit_responses.append(r)

    r = self.send_command('end')
    if r:
      commit_responses.append(r)

    return dict(request=requests, response=responses, commit_response=commit_responses)


  def get(self, command=None, prompt=None, answer=None, sendonly=False, newline=True, output=None, check_all=False):
    return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)


  def get_device_info(self):
    """show system infoコマンドを叩いてデバイス情報を収集して値を格納する

    以下の値を返却する
    network_os
    network_os_version
    network_os_model
    network_os_hostname
    """
    device_info = {}
    device_info['network_os'] = 'fujitsu_sir'

    reply = self.get('show system info')
    data = to_text(reply, errors='surrogate_or_strict').strip()

    # Si-R220C# sh system info
    # Current-time : Fri Jan  2 06:02:10 1970
    # Startup-time : Thu Jan  1 13:17:17 1970
    # System : Si-R220C
    # Serial No. : 00002982
    # ROM Ver. : 1.2
    # Firm Ver. : V35.03 NY0028 Wed Feb  1 16:57:33 JST 2012
    # Security Software Ver. : Si-R Security Software V03.03
    # Startup-config : Thu Jan  1 13:16:44 1970 config1
    # Running-config : Thu Jan  1 13:17:17 1970
    # MAC : 0017424a1e8c-0017424a1e8f
    # Memory : 128MB

    match = re.search(r'^Security Software Ver\. : (.*)', data)
    if match:
      device_info['network_os_version'] = match.group(1)

    match = re.search(r'^System : (\S+)', data)
    if match:
      device_info['network_os_model'] = match.group(1)

    # Si-Rの場合、show system infoにホスト名が含まれない
    # ここではプロンプトをそのまま代入する
    prompt = self._connection.get_prompt()
    prompt = to_text(prompt, errors='surrogate_or_strict').strip()
    device_info['network_os_hostname'] = prompt

    return device_info


  def get_device_operations(self):
    return {
      'supports_replace': False,
      'supports_commit': True,
      'supports_rollback': False,
      'supports_defaults': True,
      'supports_onbox_diff': True,
      'supports_commit_comment': False,
      'supports_multiline_delimiter': False,
      'support_match': False,
      'support_diff_ignore_lines': False,
      'supports_generate_diff': False,
    }
