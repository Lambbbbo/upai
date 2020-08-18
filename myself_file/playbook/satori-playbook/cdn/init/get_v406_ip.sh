#!/bin/bash

FILE=/tmp/ansible_init/machines/lists-cdn-v406
net_type=$1

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
  echo "$ips"
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
  echo "$ips"
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
  echo "$ips"
}

get_abroad(){
  declare -a array
  array=(`cat $FILE | grep -i abroad | awk -F "[# ]+" '{print $2}'`)
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
  echo "$ips"
}

get_scnr(){
  declare -a array
  array=(`cat $FILE | grep -i scnr | awk -F "[# ]+" '{print $2}'`)
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
  echo "$ips"
}

get_scnd(){
  declare -a array
  array=(`cat $FILE | grep -i scnd | awk -F "[# ]+" '{print $2}'`)
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
  echo "$ips"
}

get_org(){
  ip1=`get_ctc`
  ip2=`get_cnc`
  ip3=`get_cmc`
  ip4=`get_abroad`
  ips=$ip1@$ip2@$ip3@$ip4
  echo "$ips"
}

if [ x$net_type == x'CTC' ];then
  get_ctc
elif [ x$net_type == x'CNC' ];then
  get_cnc
elif [ x$net_type == x'CMC' ];then
  get_cmc
elif [ x$net_type == x'ABROAD' ];then
  get_pcw
elif [ x$net_type == x'SCND' ];then
  get_scnd
elif [ x$net_type == x'SCNR' ];then
  get_scnr
else
  get_org
fi
