#encoding:utf-8
import os

PROJECT_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
# print os.path.join(PROJECT_PATH,'cookie','sougou_weixin_day.cookie')


#save next in redis
META_NEXT_URL = 'meta_next_url'

#effective time of META_NEXT_URL
EFFECTIVE_TIME = 3600*12
