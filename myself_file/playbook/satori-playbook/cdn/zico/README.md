# zico

| tags     | feature                      |
|----------|------------------------------|
| always   | -                            |
| init     | 一些初始化                   |
| backup   | 备份                         |
| install  | 初始化安装                   |
| app      | 下载 app package             |
| config   | 同步配置                     |
| version  | 把当前版本写入 .version 文件 |
| restart  | 重启                         |
| rollback | 回滚                         |


## 部署

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=zico' -t app,config
ansible-playbook -i hosts deploy.yml -e 'node=host role=zico project=zicot' -t app,config
ansible-playbook -i hosts deploy.yml -e 'node=host role=zico project=zicod' -t app,config
ansible-playbook -i hosts deploy.yml -e 'node=host role=zico' -t redis
```

