# Ansible Collection - iida.fujitsu

test implementation of network-cli module to support fujitsu devices

動くかどうか、わかりません。
富士通機器が手元にないので、機会ができたら試してみます。

## Requirements

- Ansible 2.9 or later

## Install

1. Clone this repository

```bash
git clone https://github.com/takamitsu-iida/ansible-fujitsu-devices.git
```

1. Install collection to your personal environment

The terminal plugin will be installed to ~/.ansible/plugins/terminal

The cliconf will be installed to ~/.ansible/plugins/cliconf

The modules will be installed to ~/.ansible/plugins/modules

The module_utils will be installed to ~/.ansible/plugins/module_utils

```bash
make install
```

## Uninstall

```bash
make unintall
```

## Example

hosts

```ini
[ipcom]
iida_ve2 ansible_host=172.18.0.15
anez_ve2 ansible_host=192.168.1.78 ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q root@10.35.180.54"'
```

group_vars/ipcom/vars.yml

```yml
---

ansible_connection: network_cli

ansible_network_os: fujitsu_ipcom

# ansible_user: user
ansible_user: admin
ansible_password: "{{ vault_pass | default('') }}"

ansible_become: true
ansible_become_method: enable
ansible_become_pass: "{{ vault_become_pass | default('') }}"
```

playbook

```yml

```

execution example

```bash

```
