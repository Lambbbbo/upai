# redis

## 部署路径
`/usr/local/redis`

## 部署结构
```
/usr/local/redis/
├── bin
│   ├── redis-benchmark
│   ├── redis-check-aof
│   ├── redis-check-dump
│   ├── redis-cli
│   ├── redis-sentinel
│   └── redis-server
└── etc
    ├── redis.1003.conf
    ├── redis.1020.conf
    └── redis.1022.conf
```

## tag简述

| tags           | feature                                 |
|----------------|-----------------------------------------|
| init           | 初始化                                  |
| backup         | 备份                                    |
| install        | 初始化安装                              |
| app            | 下载 app package                        |
| config         | 同步配置                                |
| version        | 把当前版本写入 .version 文件            |
| marco          | 同步 redis-marco 启动脚本 (supervisor)  |
| shanks         | 同步 redis-shanks 启动脚本 (supervisor) |
| updns          | 同步 redis-updns 启动脚本 (supervisor)  |
| yupoo          | 同步 redis-yupoo 启动脚本 (supervisor)  |
| common         | 同步 redis-common 启动脚本 (supervisor) |
| marco.restart  | 重启  redis-marco                       |
| shanks.restart | 重启  redis-shanks                      |
| updns.restart  | 重启  redis-updns                       |
| yupoo.restart  | 重启  redis-yupoo                       |
| common.restart | 重启  redis-common                      |
| rollback       | 回滚                                    |

## 部署


```
# 边缘部署
ansible-playbook -i hosts deploy.yml -e 'node=host role=redis type=cdn' -t install 
# 中转部署
ansible-playbook -i hosts deploy.yml -e 'node=host role=redis type=406' -t install 
```

- `type=cdn` 时, 会把 `redis-marco`, `redis-yupoo`, `redis-common` 推送到机器上

- `type=406` 时, 会把 `redis-shanks`, `redis-yupoo`, `redis-common` 推送到机器上



