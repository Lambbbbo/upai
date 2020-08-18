# usopp

## 部署路径

`/usr/local/usopp`

## 部署结构

```
/usr/local
├── usopp
│   ├── UsoppGo
│   ├── config.json
│   │── ftp.upyun.com.key
│   ├── ftp.upyun.com.crt
```

## tag简述

| tags     | feature                      |
|----------|------------------------------|
| always   | -                            |
| backup   | 备份                         |
| install  | 初始化安装                   |
| app      | 下载 app package             |
| ca       | 更新ca证书
| config   | 同步配置                     |
| version  | 把当前版本写入 .version 文件 |
| restart  | 重启                         |
| rollback | 回滚                         |

## 部署

### 第一次部署

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=usopp' -t install
```

### 程序更新发布

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=usopp' -t app,config
```

