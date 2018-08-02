#!/bin/bash
#this script is used to change network settings

dir=/etc/sysconfig/network-scripts
change(){
 echo "请输入你要修改的值: [dhcp/static]";
 read pro;
 if [ $pro == static ] ;then
   sed -i "s/$bootproto/$pro/" $dir/ifcfg-eth$[choice-1];
 else
   sed -i "s/$bootproto/$pro/" $dir/ifcfg-eth$[choice-1];
   exit 0;
 fi
}

action(){
 declare -a array
 array=(`ifconfig | grep encap | awk '{ print $1 }' | grep -v "lo"`)
 echo
 echo "网卡列表:"
 
 num=1
 for card in ${array[@]}
 do
  echo "${num}--${card}"
  let num++
 done
 read -p "请选择一个网卡来修改它的配置(1-$[num-1]):" choice
 echo "你选择了 ${array[choice-1]}"

 bootproto=`cat $dir/ifcfg-${array[choice-1]} | grep -i "bootproto" | awk -F"=" '{print $2}'`
 echo
 echo "此网卡当前的bootproto是$bootproto,你想修改它吗? [y/n]"
 read anwser
  case $anwser in
   y) change;;
   n) echo;;
   *) echo "error input!" && exit 4;;
  esac

 echo -n "请输入新IP:"
 read NEWIP
  if cat $dir/ifcfg-${array[choice-1]} | grep -i "ipaddr" &> /dev/null ;then
   OLDIP=`cat $dir/ifcfg-${array[choice-1]} | grep -i "ipaddr" | sed 's/.*=\(.*\)/\1/'`
   sed -i "s/$OLDIP/$NEWIP/" $dir/ifcfg-${array[choice-1]}
  else
   echo "IPADDR=$NEWIP" >> $dir/ifcfg-${array[choice-1]}
  fi

 echo -n "请输入新的掩码:"
 read NEWMASK
  if cat $dir/ifcfg-${array[choice-1]} | grep -i "netmask" &> /dev/null ;then
   OLDMASK=`cat $dir/ifcfg-${array[choice-1]} | grep -i "netmask" | sed 's/.*=\(.*\)/\1/'`
   sed -i "s/$OLDMASK/$NEWMASK/" $dir/ifcfg-${array[choice-1]}
  else
   echo "NETMASK=$NEWMASK" >> $dir/ifcfg-${array[choice-1]}
  fi

 echo -n "请输入新的网关:"
 read NEWGATE
  if cat $dir/ifcfg-${array[choice-1]} | grep -i "gateway" &> /dev/null ;then
   OLDGATE=`cat $dir/ifcfg-${array[choice-1]} | grep -i "gateway" | sed 's/.*=\(.*\)/\1/'`
   sed -i "s/$OLDGATE/$NEWGATE/" $dir/ifcfg-${array[choice-1]}
  else
   echo "GATEWAY=$NEWGATE" >> $dir/ifcfg-${array[choice-1]}
  fi
echo
echo your network configure is:
cat $dir/ifcfg-${array[choice-1]}
}

action
echo
echo "你还需要修改其他网卡的配置吗?(y/n)"
read answer1
 until [ $answer1 == n ];do
   action
 done
echo
echo "请重启网络服务!"
