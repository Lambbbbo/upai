# updns

## 部署路径
`/usr/local/updns`

## 部署结构
```
/usr/local
├── updns
│   ├── updns
│   ├── config.json
│   ├── updns-stats
│   │   ├── ...
├── heka
│   ├── ...
│   ├── plugin
│   │   ├── updns_decoder.toml
│   │   ├── ...
├── updns-stats
│   ├── ...
├── redis
│   ├── bin
│   │   ├── redis-server
│   ├── etc
│   │   ├── redis.1020.conf
│   │   ├── redis.1023.conf
```

## tag简述

| tags     | feature                          |
|----------|----------------------------------|
| always   | -                                |
| backup   | 备份                             |
| install  | 初始化安装                       |
| app      | 下载 app package                 |
| config   | 同步配置                         |
| version  | 把当前版本写入 .version 文件     |
| heka     | 同步 heka 启动脚本 (supervisor)  |
| redis    | 同步 redis 启动脚本 (supervisor) |
| stats    | 同步 stats 启动脚本 (supervisor) |
| stunnel  | 同步 stats 启动脚本 (supervisor) |
| restart  | 重启                             |
| rollback | 回滚                             |

## 部署

updns 依赖于 `heka`，`updns-stats`,`redis`

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=redis type=updns' -t app,config 
ansible-playbook -i hosts deploy.yml -e 'node=host role=heka' -t app,config # config 会把启动脚本和配置文件也同步上去 
ansible-playbook -i hosts deploy.yml -e 'node=host role=updns-stats -t app # config 会把启动脚本也同步上去 
# 前三步并不会同步启动脚本,除非指定 config 需要在 updns role 中手动指定相关 tag
ansible-playbook -i hosts deploy.yml -e 'node=host role=updns -t app,config
ansible-playbook -i hosts deploy.yml -e 'node=host role=updns -t redis,stunnel # 同步 redis 启动脚本和 stunnel 启动脚本和配置文件
```

heka,updns-stats可以单独**app,config**进行部署，也可以只指定 **app**,到**updns role**中指定 **heka** tag

