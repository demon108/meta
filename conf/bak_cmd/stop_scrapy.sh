#!/bin/bash
#cd /disk1/you_scrapy/conf/

ps -efw |grep scrapy |grep dingyong|grep $1|awk '{print "kill -9 "$2}' |bash


