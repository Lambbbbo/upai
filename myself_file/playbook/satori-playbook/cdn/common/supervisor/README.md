# supervisord

supervisor系列，目前包括:
- logger
- purge
- falcon-agent(falcon)

主要由三个文件组成
- 二进制主文件
- 配置文件
- supervisor启动配置


## 部署结构

```
/usr/local
├── <role>
│   ├── <role>
│   ├── etc
│   │   ├── config.json
```

## tag简述

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
以 **logger** 为例

### 第一次部署

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=logger' -t install
```

### 正常情况

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=logger' -t app,config
```

