#encoding:utf-8
import json

from item import *

class MetaPipeline(object):
    
    def __init__(self):
        pass
    
    def process_item(self, item, spider):
        if isinstance(item, MetaResult):
            result = dict()
            template_name = item['template_name'] 
            record_writer = open('%s.dat'%(template_name.replace('.conf','')),'a+')
            result.update({'template_name':template_name})
            template_type = item['template_type']
            result.update({'template_type':template_type})
            keyword = item['keyword'] 
            result.update({'keyword':keyword})
            record_writer.write('keyword: %s\n'%(keyword))
            meta_pages = item['meta_pages']
            result.update({'meta_pages':meta_pages})
            domain = item['domain']
            result.update({'domain':domain})
            
            result_item = item['result_item']
            result_list = result_item.split('`')
            if 'U' in result_list:
                url = item['url']
                result.update({'url':url})
                record_writer.write('url: %s\n'%(url))
            if 'T' in result_list:
                title = item['title']
                result.update({'title':title})
                record_writer.write('title: %s\n'%(title))
            if 'D' in result_list:
                posttime = item['posttime']
                result.update({'posttime':posttime})
                record_writer.write('posttime: %s\n'%(posttime))
            if 'A' in result_list:
                author = item['author']
                result.update({'author':author})
                record_writer.write('author: %s\n'%(author))
            if 'B' in result_list:
                abstract = item['abstract']
                result.update({'abstract':abstract})
                record_writer.write('abstract: %s\n'%(abstract))
            if 'C' in result_list:
                click_count = item['click_count']
                result.update({'click_count':click_count})
                record_writer.write('click_count: %s\n'%(click_count))
            if 'R' in result_list:
                comment_count = item['comment_count']
                result.update({'comment_count':comment_count})
                record_writer.write('comment_count: %s\n'%(comment_count))
            if 'P' in result_list:
                copy_url = item['copy_url']
                result.update({'copy_url':copy_url})
                record_writer.write('copy_url: %s\n'%(copy_url))
            if 'I' in result_list:
                id = item['id']
                result.update({'id':id})
            if 'S' in result_list:
                source = item['source']
                result.update({'source':source})
                record_writer.write('source: %s\n'%(source))
            record_writer.write('\n')
            record_writer.flush()
            
            
