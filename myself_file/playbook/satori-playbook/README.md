# UPYUN SATORI Ansible Playbook
------
又拍云satori任务系统使用的playbook仓库。

## 环境配置

### 依赖

 - python 2.7
 - ansible 2.4.1

### 配置
建议在 Ansible 执行的机器，添加一个全局配置文件 `~/.ansible.cfg`：
```
[defaults]
host_key_checking = False # 关闭 host key 检查

# 开启 fact 缓存，能够加快执行速度
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/facts_cache

# two hours timeout
fact_caching_timeout = 7200
```

## 目录结构
```bash
├── README.md
├── install.yml                # CDN业务安装入口文件
├── release.yml                # CDN业务发布入口文件
├── rollback.yml               # CDN业务回滚入口文件
├── action_plugins             # Action Plugin 目录。
│   └── libenc.so
│   └── fetch_pack.py
├── group_vars
│   └── all                    # 全局默认变量文件。
├── inventory                  # 动态inventory。
├── library                    # Ansible Module 目录。
│   └── fetch_pack.py
│   └── fetch_meta.py
├── common                     # 通用任务
│   └── ping.yml
│   └── port_detect.yml
│   └── ...
├── maintenance                # 运维相关的维护任务
│   └── marco_restart.yml
│   └── timesync.yml
│   └── ...
├── cdn                        # upyun cdn各组件相关任务
│   └── marco
    │   └── tasks
    │       └── check.yml
    │       └── config.yml
│   └── bepo
│   └── ...
```
