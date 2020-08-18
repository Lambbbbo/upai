#!/bin/bash

# Copyright (C) UPYUN, Inc.

ulimit -S -c 0
ulimit -n 65535
ulimit -f unlimited
ulimit -u unlimited

PROG={{ project }}
NGINX_BASE=/usr/local/$PROG/nginx
NGINX_CONFIG=$NGINX_BASE/conf/nginx.conf
NGINX_CMD=$NGINX_BASE/sbin/nginx
NGINX_PID=/var/run/$PROG.pid
NGINX_LOCK=/var/lock/subsys/$PROG
LOG_DIR=/disk/ssd1/logs

RETVAL=0
[ -d $NGINX_BASE ] || exit 1
[ -d $LOG_DIR ] || mkdir $LOG_DIR

# Source function library.
. /etc/rc.d/init.d/functions

# Source networking configuration.
. /etc/sysconfig/network

# Check that networking is up.
[ ${NETWORKING} = "no" ] && exit 0


start() {
   if [ -e $NGINX_PID ];then
       echo "nginx already running...."
       RETVAL=1
   fi
   echo -n $"Starting $PROG: "
   $NGINX_CMD -c $NGINX_CONFIG
   RETVAL=$?
   echo
   [ $RETVAL = 0 ] && touch $NGINX_LOCK
   return $RETVAL
}

# Stop nginx daemons functions.
stop() {
    if [ -e $NGINX_PID ];then
        echo -n $"Stopping $PROG: "
        master_pid=`cat $NGINX_PID`
        master_ppid=`ps -o ppid= -p $master_pid`
        # parent of master is the init process?
        if [ $master_ppid == "1" ]; then
            kill -TERM $master_pid
        else
            # hot update
            kill -TERM $master_ppid
            sleep 1
            kill -TERM $master_pid
        fi
   else
      echo "nginx already stopped...."
      return 1
   fi
}

# reload nginx service functions.
reload() {
    echo -n $"Reloading $PROG: "
    $NGINX_CMD -s reload
    RETVAL=$?
    echo

}

# See how we were called.
case "$1" in
start)
        start
        ;;

stop)
        stop
        ;;

reload)
        reload
        ;;

restart)
        stop
        sleep 1
        start
        ;;
status)
        pidof $NGINX_CMD
        RETVAL=$?
        ;;
*)
        echo $"Usage: $PROG {start|stop|restart|reload|status|help}"
        exit 1
esac

exit $RETVAL
