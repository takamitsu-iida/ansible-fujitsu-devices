# ansible-fujitsu-devices

test implementation of network-cli module to support fujitsu devices

IPCOMは動きました。

Si-RとSR-Sは手元にないため動作確認でいません。
機会があったら確認します。

## Requirements

- Ansible 2.9 or later

## Install

### Clone this repository

```bash
git clone https://github.com/takamitsu-iida/ansible-fujitsu-devices.git
```

### Install to your personal environment

`make install`  or  `ansible-playbook installer/install.yml`

This command will install modules and plugins to `~/.ansible/plugins/` directory.

## Uninstall

`make unintall`  or  `ansible-playbook installer/uninstall.yml`

This command will remove files from `~/.ansible/plugins/` directory.
