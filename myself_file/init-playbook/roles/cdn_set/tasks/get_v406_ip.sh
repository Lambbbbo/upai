#!/bin/bash

FILE=/tmp/ansible_init/machines/lists-cdn-v406

get_ctc(){
  declare -a array
  array=(`cat $FILE | grep -i ctc | awk -F "[# ]+" '{print $2}'`)
  length=${#array[@]}
  num=1
  ips=''
  for ip in ${array[@]};do
    if [ $num -lt $length ];then
      IP=${ip}:406@
    else
      IP=${ip}:406
    fi
    ips=$ips$IP
    let num++
  done
  echo CTC: \"$ips\" > roles/cdn_set/vars/main.yml
}

get_cnc(){
  declare -a array
  array=(`cat $FILE | grep -i cnc | awk -F "[# ]+" '{print $2}'`)
  length=${#array[@]}
  num=1
  ips=''
  for ip in ${array[@]};do
    if [ $num -lt $length ];then
      IP=${ip}:406@
    else
      IP=${ip}:406
    fi
    ips=$ips$IP
    let num++
  done
  echo CNC: \"$ips\" >> roles/cdn_set/vars/main.yml
}

get_cmc(){
  declare -a array
  array=(`cat $FILE | grep -i cmc | awk -F "[# ]+" '{print $2}'`)
  length=${#array[@]}
  num=1
  ips=''
  for ip in ${array[@]};do
    if [ $num -lt $length ];then
      IP=${ip}:406@
    else
      IP=${ip}:406
    fi
    ips=$ips$IP
    let num++
  done
  echo CMC: \"$ips\" >> roles/cdn_set/vars/main.yml
}

get_org(){
  ips=`awk -F '"' '{print $2}' roles/cdn_set/vars/main.yml | xargs | sed "s/ /@/g"`
  echo ORG: \"$ips\" >> roles/cdn_set/vars/main.yml
}

get_ctc
get_cnc
get_cmc
get_org
