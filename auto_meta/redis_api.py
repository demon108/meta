import redis

def connect():
    handle = redis.StrictRedis('127.0.0.1',port=6379,db='0')
    return handle

def delete_keys(handle,key):
    handle.delete(key)
    
def add_zset(handle,key,score,value):
    handle.zadd(key,score,value)
    
def fetch_zset(handle,key,num):
    keywords = handle.zrevrange(key,0,num)
    for keyword in keywords:
        handle.zrem(key,keyword)
    return keywords
