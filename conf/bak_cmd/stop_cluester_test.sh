#/bin/bash
cd /home/dingyong/meta/conf/
/bin/python stop_crawler.py baidu_news_copy.conf
date=`date +%F`
mv baidu_news_copy.log "baidu_news_copy.log.$date"
