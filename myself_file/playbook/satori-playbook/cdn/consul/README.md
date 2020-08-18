该项目用来推送直播less项目的相关组件consul

推送命令：  
ansible-playbook -i lists deploy.yml -e 'node=host role=consul type=cdn|origin' -t install  
与less项目一致，type类型分为edge边缘节点以及origin源站。  
