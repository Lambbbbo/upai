# zicogo

## tag简述

| tags    | feature                                          |
|---------|--------------------------------------------------|
| always  | -                                                |
| backup  | 备份                                             |
| install | 初始化安装                                       |
| app     | 下载 app package                                 |
| config  | 同步配置                                         |
| version | 把当前版本写入 .version 文件                     |
| restart | 重启, **edge**: supervisor ; **transfer**: nginx |

## 部署

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=zicogo type=cdn' -t app,config
ansible-playbook -i hosts deploy.yml -e 'node=host role=zicogo type=406' -t app,config
```


