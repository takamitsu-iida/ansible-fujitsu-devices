# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""plugins/terminal/fujitsu_ipcom.py

terminal plugin for fujitsu_ipcom

Takamitsu IIDA (@takamitsu-iida)
"""

import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.terminal import TerminalBase
from ansible.module_utils._text import to_text, to_bytes


class TerminalModule(TerminalBase):
  """TerminalModule for Fujitsu IPCOM
  """

  # ipcom#
  # ipcom>
  # ipcom(edit)#
  terminal_stdout_re = [
    re.compile(br"[\r\n]?[\w\+\-\.:\/\[\]]+(?:\([^\)]+\)){0,3}(?:[>#]) ?$"),
    re.compile(br"\?\s+\(y\|\[n\]\):$"),
    re.compile(br"\?\s+\(\[y\]\|n\):$")
  ]

  terminal_stderr_re = [
    # ABORT is expected condition, not error
    # re.compile(br"\<ABORT\>.*", re.M),
    re.compile(br"Unknown commands or command parameters are insufficient", re.M),
    re.compile(br"\<ERROR\>.*", re.M),
    re.compile(br"Permission denied, please try again", re.M)
  ]

  def on_open_shell(self):
    """on open shell
    disable pager using 'terminal pager disable' commnad.
    """
    try:
      self._exec_cli_command(b'terminal pager disable')
    except AnsibleConnectionFailure:
      raise AnsibleConnectionFailure('unable to set terminal parameters')


  def on_become(self, passwd=None):
    """on become
    escalate privilege mode using 'admin' command.
    """
    prompt = self._get_prompt()
    if prompt is None or prompt.strip().endswith(b'#'):
      return

    cmd = {u'command': u'admin'}
    if passwd:
      cmd[u'prompt'] = to_text(r"(?i)[\r\n]?Password: $", errors='surrogate_or_strict')
      cmd[u'answer'] = passwd
      cmd[u'prompt_retry_check'] = True

    try:
      self._exec_cli_command(to_bytes(json.dumps(cmd), errors='surrogate_or_strict'))
      prompt = self._get_prompt()
      if prompt is None or not prompt.strip().endswith(b'#'):
        raise AnsibleConnectionFailure('failed to elevate privilege to enable mode still at prompt [%s]' % prompt)
    except AnsibleConnectionFailure as e:
      prompt = self._get_prompt()
      raise AnsibleConnectionFailure('unable to elevate privilege to enable mode, at prompt [%s] with error: %s' % (prompt, e.message))


  def on_unbecome(self):
    """on unbecome
    exit from privilege mode using 'exit' command.
    """
    prompt = self._get_prompt()
    if prompt is None:  # terminal hang up?
      return

    prompt = prompt.strip()

    if b'(config' in prompt or b'(edit' in prompt:
      # endコマンドでコンフィグモードを抜ける
      self._exec_cli_command(b'end')
      prompt = self._get_prompt()
      if b'(y|[n]):' in prompt:
        self._exec_cli_command(b'y')

    if prompt.endswith(b'#'):
      self._exec_cli_command(b'exit')
