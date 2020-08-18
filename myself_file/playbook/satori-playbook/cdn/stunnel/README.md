# stunnel

## 部署路径
`/usr/local/stunnel`

## 部署结构
```
/usr/local/stunnel/
├── bin
│   ├── stunnel
│   └── stunnel3
├── etc
│   └── stunnel
│       ├── stunnel.conf
│       ├── stunnel.conf-sample
│       └── ...
├── lib
│   └── ...
└── share
│   └── ...
```

## tag简述

| tags     | feature                          |
|----------|----------------------------------|
| always   | -                                |
| backup   | 备份                             |
| install  | 初始化安装                       |
| app      | 下载 app package                 |
| config   | 同步配置(包括配置文件与启动脚本) |
| version  | 把当前版本写入 .version 文件     |
| restart  | 重启                             |
| rollback | 回滚                             |

## 部署

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=stunnel' -t app,config 
# OR
ansible-playbook -i hosts deploy.yml -e 'node=host role=stunnel' -t install
```

注：部署 **updns** 时可以不指定 **config**, 而是到 updns role 下单独指定 stunnel tag
