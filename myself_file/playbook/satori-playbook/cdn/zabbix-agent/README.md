ansible-playbook -i hosts deploy.yml -e "role=zabbix-agent node=host" -t install

proxy地址列表：  
`k8s-ingress.service.upyun:30101`  #数据中心机器使用，华通、临安两个数据中心使用该proxy，推送时指定  
`k8s-ingress.service.upyun:30102`  #数据中心机器使用，福地数据中心使用该proxy，推送时指定  
`zbx-proxy.x.upyun.com:3103`       #外网CDN机器使用，移动、联通节点使用该proxy，推送时指定  
`zbx-proxy.x.upyun.com:3104`       #外网CDN机器使用，电信、中转及其他运营商使用该proxy，推送时指定  
