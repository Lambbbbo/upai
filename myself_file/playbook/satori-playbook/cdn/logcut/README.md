# logcut

## 部署路径

`/usr/local/logcut`

## 部署结构

```
/usr/local
├── logcut
│   ├── logcut
│   ├── etc
│   │   ├── config.json
```

## tag简述

| tags     | feature                      |
|----------|------------------------------|
| always   | -                            |
| backup   | 备份                         |
| install  | 初始化安装                   |
| app      | 下载 app package             |
| config   | 同步配置                     |
| version  | 把当前版本写入 .version 文件 |
| restart  | 重启                         |
| rollback | 回滚                         |

## 部署

### 第一次部署

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=logcut' -t install
```

### 正常情况

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=logcut' -t app,config
```

