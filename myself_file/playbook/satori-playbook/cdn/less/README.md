该playbook用来推送直播less项目。

ansible-playbook -i lists deploy.yml -e "node=host role=less type=cdn|origin" -t install  
该推送命令安装less项目，其中type 有2个选项，edge为边缘节点，origin为源站。  

##  推送
对于less项目，有4个二进制文件，开发单独编译打包，所以推送时也可以单独推送某一二进制文件，如：  
>  只推送less-server组件  
`ansible-playbook -i lists deploy.yml -e "node=host role=less type=cdn|origin" -t less-server`  
>  只推送less-logger组件  
`ansible-playbook -i lists deploy.yml -e "node=host role=less type=cdn|origin" -t less-logger`  
>  只推送less-log-stat组件  
`ansible-playbook -i lists deploy.yml -e "node=host role=less type=cdn|origin" -t less-log-stat`  
>  只推送less-log-sender组件  
`ansible-playbook -i lists deploy.yml -e "node=host role=less type=cdn|origin" -t less-log-sender`  

##  回退
对于回退，有2个tag， rollback和 min_rollback，区别在于：  
rollback 回退整包  
min_rollback 回退单个组件  
