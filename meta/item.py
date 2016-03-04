#encoding:utf-8
from scrapy.item import Item, Field

class MetaResult(Item):
    result_item = Field()       #提取结果列表
    template_name = Field()     #模板名
    template_type = Field()     #模板类型
    keyword = Field()           #查询词
    meta_pages = Field()        #meta页码
    title = Field()             #标题
    abstract = Field()          #摘要
    posttime = Field()          #发布时间
    url = Field()               #链接
    copy_url = Field()       #相似链接
    author = Field()            #作者
    source = Field()            #来源
    id = Field()                #微信的openid
    repost_count = Field()      #转发数
    comment_count = Field()     #评论数
    click_count = Field()       #点击数
    like_count = Field()        #点赞数
    read_count = Field()        #阅读数
    domain = Field()            #网站英文域名
    metatime = Field()          #meta时间
    searchtime = Field()        #关键词搜索时间
    state = Field()             #相似链接抓取状态:0未抓取1正在抓取2抓取完成3没有相似链接
    meta_ip = Field()           #启动meta程序的机器ip
    parent_url = Field()        #从meta库中取出cluster_url的url字段值，用于更新该url对应的state
    
