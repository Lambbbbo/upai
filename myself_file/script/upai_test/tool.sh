#!/bin/bash

ip=""
sign="0"
domain=""
dt=`date -u +%a," "%d" "%b" "%Y" "%T" "GMT`
secret=`echo -n ${PASSWORD} | md5sum | awk '{print $1}'`
method=""
verbose="off"

usage(){
    cat << EOF
    before use this shell script,please do some pre_work(export env variable):
	export USERNAME=<operator_name>
	export PASSWORD=<operator_password>
	export BUCKET=<bucket>

    usage: `basename $0` [-u | -d | -g | -r | -v | -h ]
    -u : upload file to Cloud Storage，-u PATTERN LOCAL_FILE_PATH REMOTE_FILE_PATH <ip=x.x.x.x>, eg.(-u rest /root/1.png /pic/1.png)
	 ftp|FTP : -u ftp local_file_path remote_file_path
	 rest|REST : -u rest local_file_path remote_file_path
	 form|FORM : -u form local_file_path remote_file_path
         ip : optional, you can specify a server ip to request. or not specify,`basename $0` will use the dns lookup ip.

    -d : download file from  Cloud Storage， -d PATTERN PATTERN LOCAL_FILE_PATH REMOTE_FILE_PATH <ip=x.x.x.x>, eg.(-d rest /home/download.png /pic/1.png)
	 ftp|FTP : -u ftp local_file_path remote_file_path
	 rest|REST : -u rest local_file_path remote_file_path
         ip : optional, you can specify a server ip to request. or not specify,`basename $0` will use the dns lookup ip.

    -g : get file from source station, -g URL LOCAL_FILE_PATH <ip=x.x.x.x>，eg.(-g http://www.163.com/pic/1.jpg /download/1.jpg)
         ip : optional, you can specify a server ip to request. or not specify,`basename $0` will use the dns lookup ip.

    -r : refresh cdn_cache, -d URL , eg.(-r http://www.163.com/pic/1.png)
    -v : verbose, view detail
    -h : help
EOF
}

auth(){
    if [ $method == ftp ] || [ $method == FTP ];then
	ftp_user=${USERNAME}"/"${BUCKET}
    elif [ $method == rest ] || [ $method == REST ];then
	auth_h=`echo -n "${USERNAME}:${PASSWORD}" | base64`
    elif [ $method == form ] || [ $method == FORM ];then
	dt_s=`date +%s -d "$dt"`
	dt_s_e=`expr $dt_s + 3600`
	file_md5=`md5sum $l_path | awk '{print $1}'`
#	secret=`echo -n ${PASSWORD} | md5sum | awk '{print $1}'`
	policy={\"bucket\":\"$BUCKET\",\"save-key\":\"$r_path\",\"expiration\":\"${dt_s_e}\",\"date\":\"${dt}\",\"content-md5\":\"${file_md5}\"}
	policy_b=`echo -n $policy | base64`
	policy_r=`echo ${policy_b} | sed "s# ##g"`
	sign=`echo -n "POST&/${BUCKET}&${dt}&${policy_r}&${file_md5}" | openssl sha1 -hmac "${secret}" -binary | base64`
    fi
}

upload(){
    if [ $method == ftp ] || [ $method == FTP ];then
	if [ $sign -eq 1 ];then
	    ftp -inv << EOF
            open $ip
            user $ftp_user $PASSWORD
            binary
            put $l_path $r_path
EOF
            echo
	else
	    ftp -inv << EOF
	    open v0.ftp.upyun.com
	    user $ftp_user $PASSWORD
	    binary
	    put $l_path $r_path
EOF
	    echo
	    domain="v0.ftp.upyun.com"
        fi
    elif [ $method == rest ] || [ $method == REST ];then
 	if [ $sign -eq 1 ];then
	    curl -X PUT http://${ip}/${BUCKET}${r_path} -H "Host:v0.api.upyun.com" -H "Authorization: Basic ${auth_h}" -H "Date: <${dt}>" -H "Content-Length: ${file_len}" -T "${l_path}" -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n -v -s  > /tmp/http_res.txt 2>&1
	    domain="v0.api.upyun.com"
            echo -e "\033[41;37m request domain is ${domain} \033[0m"
            echo -e "\033[41;37m request ip is ${ip} \033[0m"
            echo
	else
 	    curl -X PUT http://v0.api.upyun.com/${BUCKET}${r_path} -H "Authorization: Basic ${auth_h}" -H "Date: <${dt}>" -H "Content-Length: ${file_len}" -T "${l_path}" -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n -v -s  > /tmp/http_res.txt 2>&1
	    domain="v0.api.upyun.com"
	    ip=`cat /tmp/http_res.txt | awk '{for(i=1;i<=NF;i++)if($i=="Trying")print $(i+1)}' | awk -F'.' 'OFS="."{print $1,$2,$3,$4}'`
	    echo -e "\033[41;37m request domain is ${domain} \033[0m"
	    echo -e "\033[41;37m request ip is ${ip} \033[0m"
	    echo
	fi
    elif [ $method == form ] || [ $method == FORM ];then
	if [ $sign -eq 1 ];then
	    curl http://${ip}/${BUCKET} -H "Host:v0.api.upyun.com" -F authorization="UPYUN ${USERNAME}:${sign}" -F file=@${l_path} -F policy=${policy_r} -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n -v -s > /tmp/http_res.txt 2>&1
	    domain="v0.api.upyun.com"
            echo -e "\033[41;37m request domain is ${domain} \033[0m"
            echo -e "\033[41;37m request ip is ${ip} \033[0m"
            echo
	else
	    curl http://v0.api.upyun.com/${BUCKET} -F authorization="UPYUN ${USERNAME}:${sign}" -F file=@${l_path} -F policy=${policy_r} -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n -v -s > /tmp/http_res.txt 2>&1
	    domain="v0.api.upyun.com"
	    ip=`cat /tmp/http_res.txt | awk '{for(i=1;i<=NF;i++)if($i=="Trying")print $(i+1)}' | awk -F'.' 'OFS="."{print $1,$2,$3,$4}'`
	    echo -e "\033[41;37m request domain is ${domain} \033[0m"
            echo -e "\033[41;37m request ip is ${ip} \033[0m"
	    echo
	fi
    fi
}

download(){
    if [ $method == ftp ] || [ $method == FTP ];then
	if [ $sign -eq 1 ];then 
	    ftp -inv << EOF
	    open $ip
	    user $ftp_user $PASSWORD
	    binary
	    get $r_path $l_path
EOF
	    echo
	    domain="v0.ftp.upyun.com"
	else
	    ftp -inv << EOF
            open v0.ftp.upyun.com
            user $ftp_user $PASSWORD
            binary
            get $r_path $l_path
EOF
            echo
            domain="v0.ftp.upyun.com"
	fi
    elif [ $method == rest ] || [ $method == REST ];then
	if [ $sign -eq 1 ];then
      	    curl -X GET http://${ip}/${BUCKET}${r_path} -H "Host:v0.api.upyun.com" -H "Authorization: Basic ${auth_h}" -o $l_path -s -v -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n > /tmp/http_res.txt 2>&1
            domain="v0.api.upyun.com"
            echo -e "\033[41;37m request domain is ${domain} \033[0m"
            echo -e "\033[41;37m request ip is ${ip} \033[0m"
            echo
	else
	    curl -X GET http://v0.api.upyun.com/${BUCKET}${r_path} -H "Authorization: Basic ${auth_h}" -o $l_path -s -v -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n > /tmp/http_res.txt 2>&1
	    domain="v0.api.upyun.com"
	    ip=`cat /tmp/http_res.txt | awk '{for(i=1;i<=NF;i++)if($i=="Trying")print $(i+1)}' | awk -F'.' 'OFS="."{print $1,$2,$3,$4}'`
	    echo -e "\033[41;37m request domain is ${domain} \033[0m"
            echo -e "\033[41;37m request ip is ${ip} \033[0m"
	    echo
	fi
    fi
}

get(){
	if [ $sign -eq 1 ];then
	    curl -X GET ${req_url} -o ${l_path} -H "Host:${host}" -s -v -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n > /tmp/http_res.txt 2>&1
            domain=$host 
            echo -e "\033[41;37m request domain is ${domain} \033[0m"
            echo -e "\033[41;37m request ip is ${ip} \033[0m"
            echo
	else
    	    curl -X GET ${url} -o ${l_path} -s -v -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n > /tmp/http_res.txt 2>&1
    	    domain=`echo "${url}" | awk -F "[/]+" '{print $2}'`
    	    ip=`cat /tmp/http_res.txt | awk '{for(i=1;i<=NF;i++)if($i=="Trying")print $(i+1)}' | awk -F'.' 'OFS="."{print $1,$2,$3,$4}'`
	    echo -e "\033[41;37m request domain is ${domain} \033[0m"
            echo -e "\033[41;37m request ip is ${ip} \033[0m"
	    echo
	fi
}

info(){
    if [[ $method == ftp ]] || [[ $method == FTP ]];then
    	echo 
    else
    	if [ $verbose == off ];then
	    echo -e "\033[31m-------------server response-----------\033[0m"
  	    echo
            cat /tmp/http_res.txt | grep '<' | egrep "HTTP/1.1|Server" 
            echo
            echo -e "\033[31m-------------time information----------\033[0m"
	    echo
            cat /tmp/http_res.txt | egrep "dns_lookup|time" | sed "s/.*dns_lookup\(.*\)/dns_lookup\1/"
	    echo
            rm -f /tmp/http_res.txt
    	elif [ $verbose == on ];then
	    echo -e  "\033[31m-------------server response-----------\033[0m"
	    echo
	    cat /tmp/http_res.txt | egrep "<|>"
	    echo
	    echo -e "\033[31m-------------time information----------\033[0m"
	    echo
            cat /tmp/http_res.txt | egrep "dns_lookup|time" | sed "s/.*dns_lookup\(.*\)/dns_lookup\1/"
	    echo
            rm -f /tmp/http_res.txt
    	fi
    fi
}

refresh(){
    key="${url}&${BUCKET}&${dt}&${secret}"
    sign=`echo -n "$key" | md5sum | awk '{print $1}'`
    curl -X POST http://purge.upyun.com/purge/ -H "Authorization: UPYUN ${BUCKET}:${USERNAME}:${sign}" -H "Date: ${dt}" -F "purge=${url}" -v -s -w dns_lookup:%{time_namelookup}\\ntime_connect:%{time_connect}\\ntime_appconnect:%{time_appconnect}\\ntime_pretransfer:%{time_pretransfer}\\ntime_redirect:%{time_redirect}\\ntime_starttransfer:%{time_starttransfer}\\ntotal_time:%{time_total}\\n > /tmp/http_res.txt 2>&1
    domain="purge.upyun.com"
    ip=`cat /tmp/http_res.txt | awk '{for(i=1;i<=NF;i++)if($i=="Trying")print $(i+1)}' | awk -F'.' 'OFS="."{print $1,$2,$3,$4}'`
    echo -e "\033[41;37m request domain is ${domain} \033[0m"
    echo -e "\033[41;37m request ip is ${ip} \033[0m"
    echo
}

#iptest(){
#    ping_result=`ping -c 4 $ip | egrep "from|transmitted"`
#    echo "----------ping test complete!----------"
#    echo 
#    echo "$ping_result"
#    echo 
#    echo "--------traceroute result below--------"
#    tracepath -n $ip
#}

net_test(){
    res_8=`dig $domain @8.8.8.8 | sed -n "/ANSWER SECTION/,/^$/p" | sed "1d"`
    res_114=`dig $domain @114.114.114.114 | sed -n "/ANSWER SECTION/,/^$/p" | sed "1d"`
    res_119=`dig $domain @119.29.29.29 | sed -n "/ANSWER SECTION/,/^$/p" | sed "1d"`
    res_223=`dig $domain @223.5.5.5 | sed -n "/ANSWER SECTION/,/^$/p" | sed "1d"`
    ns1_res=`dig $domain @ns1.ialloc.com | sed -n "/ANSWER SECTION/,/^$/p" | sed "1d"`
    if [ ${ip} ];then
        ping_result=`ping -c 4 ${ip} | egrep "from|transmitted"`
    else
	ping_result=`ping -c 4 ${domain} | egrep "from|transmitted"`
    fi
    echo -e "\033[31m----------ping result----------\033[0m"
    echo 
    echo "$ping_result"
    echo
    echo -e "\033[31m--------dns_lookup result of 8.8.8.8--------\033[0m"
    echo
    echo "$res_8"
    echo
    echo -e "\033[31m--------dns_lookup result of 114.114.114.114--------\033[0m"
    echo
    echo "$res_114"
    echo
    echo -e "\033[31m--------dns_lookup result of 119.29.29.29--------\033[0m"
    echo
    echo "$res_119"
    echo
    echo -e "\033[31m--------dns_lookup result of 223.5.5.5--------\033[0m"
    echo
    echo "$res_223"
    echo 
    echo -e "\033[31m--------dns_lookup result of ns1.ialloc.com--------\033[0m"
    echo
    echo "$ns1_res"
    echo
    echo -e "\033[31m----------traceroute result----------\033[0m"
    echo
    if [ ${ip} ];then
	traceroute -n ${ip}
    else
	traceroute -n ${domain}
    fi
    echo
}

if [ $# -lt 1 ];then
    usage
fi

until [ $# -eq 0 ];do
case "$1" in 
    -u)
        method=$2
	if [ $# -lt 4 ];then
	    echo "error! -u option need at least 3 parameters, METHOD,local_file_path,remote_file_path"
	    exit 5
	fi
	if [ $method == ftp ] || [ $method == FTP ];then
	    l_path=$3
	    r_path=$4
	    auth
	elif [ $method == rest ] || [ $method == REST ];then
	    l_path=$3
	    r_path=$4
	    auth
	    file_len=`ls -l $3 | awk '{print $5}'`
	elif [ $method == form ] || [ $method == FORM ];then
	    l_path=$3
	    r_path=$4
	    auth
	fi
        echo "$@" | grep -q 'ip='
        if [ $? -eq 0 ];then
	    ip=`echo $@ | awk -F "[ =]+" '{print $(NF-1)}'`
	    sign=1
	    shift 5
 	else
	    shift 4
	fi
	upload
	net_test
	if [ -z $1 ];then
 	    if [ $method == rest ] || [ $method == REST ] || [ $method == form ] || [ $method == FORM ];then
	    	info
	    fi
	fi
	;;
    -d)
	method=$2
	if [ $# -lt 4 ];then
            echo "error! -d option need at least 3 parameters, METHOD,local_file_path,remote_file_path"
            exit 5
        fi
	if [ $method == ftp ] || [ $method == FTP ];then
	    r_path=$4
	    l_path=$3
	    auth
	elif [ $method == rest ] || [ $method == REST ];then
	    l_path=$3
	    r_path=$4
	    auth
	fi
 	echo "$@" | grep -q 'ip='
   	if [ $? -eq 0 ];then
	    ip=`echo $@ | awk -F "[ =]+" '{print $(NF-1)}'`
	    sign=1
            shift 5
        else
	    shift 4
	fi
	download
	net_test
	if [ -z $1 ];then
	    if [ $method == rest ] || [ $method == REST ];then 
            	info
	    fi
        fi
	;;
    -g)
	url=$2
	l_path=$3
	get
	net_test
	echo "$@" | grep -q 'ip='
	if [ $? -eq 0 ];then
	    host=`echo $url | awk -F "[ /]+" '{print $2}'`
	    ip=`echo $@ | awk -F "[ =]+" '{print $(NF-1)}'`
	    req_uri=`echo $url | sed "s/${host}/${ip}/"`
	    sign=1
            shift 4
        else
	    shift 3
	fi
	if [ -z $1 ];then
            info
        fi
	;;
    -r)
	url=$2
	refresh
	net_test
	shift 2
	if [ -z $1 ];then
	    info
	fi
	;;
    -v)
	verbose="on"
	info
	shift 1
	;;
    -h)
	usage
	shift 1
	;;
     *)
	echo "Invalid option: $1"
	usage
	exit 6
	;;
esac
done
