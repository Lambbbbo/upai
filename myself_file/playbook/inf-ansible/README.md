# UPYUN INFRASTRUCTURE Ansible Playbook

## Roles

### redis-sentinel

> sentinel

- 192.168.12.11:3000
- 192.168.12.12:3000
- 192.168.12.13:3000
- 192.168.12.14:3000

> redis

| name | port | default master | default slaves |
|------|------|----------------|----------------|
| master00 | 3001 | 192.168.12.12 | 12.11, 12.13, 12.14 |
| master01 | 3002 | 192.168.12.13 | 12.11, 12.12, 12.14 |
| master02 | 3003 | 192.168.12.14 | 12.11, 12.12, 12.13 |
| master03 | 3004 | 192.168.12.11 | 12.12, 12.13, 12.14 |

> ansible

```
ansible-playbook -i inventories/hosts -e 'node=REDIS-SENTINEL role=redis-sentinel' deploy.yml -t config
```

## files

所有下载包都可以通过以下地址下载：

- 10.0.5.110:8000/inf/xxx.tar.gz
