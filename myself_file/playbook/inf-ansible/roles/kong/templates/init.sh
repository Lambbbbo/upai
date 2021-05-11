#!/bin/bash

# Copyright (C) UPYUN, Inc.

ulimit -S -c 0
ulimit -n 65535
ulimit -f unlimited
ulimit -u unlimited

KONG_DIR={{ main_path }}
KONG_CLI=$KONG_DIR/bin/kong

case "$1" in
  start)
        echo -n "Starting kong: "
        if $KONG_CLI start -c $KONG_DIR/kong.conf --nginx-conf $KONG_DIR/nginx.conf.template
        then
                echo "ok"
        else
                echo "failed"
        fi
        ;;
  stop)
        echo -n "Stopping kong: "
        if $KONG_CLI stop
        then
                echo "ok"
        else
                echo "failed"
        fi
        ;;
  restart)
        ${0} stop
        ${0} start
        ;;
  *)
        echo "Usage: /etc/init.d/kong {start|stop|restart}" >&2
        exit 1
        ;;
esac

exit 0