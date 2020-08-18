# nginx

nginx系列，目前包括:
- marco
- kuzan
- vista
- ohm
- shanks

主要由三个部分组成
- 二进制文件,包括在 core package 中
- lua 文件,包括在 app package 中
- 配置文件


## 部署结构

```
/usr/local
├── <role>
│   ├── nginx
│   ├── app
│   │   ├── etc
|   │   │   ├── config.lua
│   │   ├── src
│   ├── conf
│   │   ├── <role>
|   │   │   ├── upstream.conf
```

## tag简述

| tags     | feature                      |
|----------|------------------------------|
| always   | -                            |
| init     | 一些初始化                   |
| backup   | 备份                         |
| install  | 初始化安装                   |
| app      | 下载 app package             |
| core     | 下载 core package            |
| config   | 同步配置                     |
| version  | 把当前版本写入 .version 文件 |
| reload   | 重启                         |
| upgrade  | 热更新                       |
| quit     | 退出旧的 master 进程         |
| rollback | 回滚                         |

## 部署
以 **marco** 为例

### 第一次部署

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=marco' -t install
```

### 正常情况

```
ansible-playbook -i hosts deploy.yml -e 'node=host role=marco' -t app,core,config
```

### 重启情况
- 更新了 **core**

  ```
  ansible-playbook -i hosts deploy.yml -e 'node=host role=marco' -t quit # 如果有旧 master 未退出先进行 quit 操作
  ansible-playbook -i hosts deploy.yml -e 'node=host role=marco' -t upgrade
  ```

- 只更新 **app**

  ```
  ansible-playbook -i hosts deploy.yml -e 'node=host role=marco' -t reload
  ```
