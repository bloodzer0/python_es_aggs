# /usr/bin/env python3
# -*- coding: utf-8 -*-

# Time: 2020/3/15 5:44 下午
# Author: bloodzer0
# File: api_monitor.py
# 微信公众号: heysec
# WeChat: Lzero2012

'''
从ES从获取数据，对API进行监控，超过阈值就报警
'''

from elasticsearch import Elasticsearch
import requests
import json

rule_file = open('rules/rules.txt','r')
whitelist_ip = open('rules/whiteip.txt','r')

'''
通过钉钉报警
'''
def alarm(alarm_data):
    try:
        dingding_url = "https://oapi.dingtalk.com/robot/send?access_token=dingtalk_token"
        headers = {'Content-Type': "application/json"}
        data = {"msgtype": "text", "text": {"content": alarm_data}}
        requests.post(dingding_url,headers=headers, data=json.dumps(data),verify=True)
    except Exception as e:
        print("请求钉钉出错")

'''
从es中获取数据
'''
def get_results(api_keyword,monitor_time,alarm_number,index_name):
    data = '''
    {
    "size": 0,
      "query": {
        "bool": {
          "must": [
            {"term": {
              "request_api.keyword": {
                "value": "%s"
              }
            }}
          ],
          "filter": {
            "range": {
              "@timestamp": {
                "gte": "now-%s",
                "lte": "now"
              }
            }
          }
        }
      },
      "aggs": {
        "ip_count": {
          "terms": {
            "field": "remote_addr.keyword",
            "size": 1000000
          }
        }
      }
    }
    ''' %(api_keyword,monitor_time)

    es_host = "es地址"
    whitelist_ip = []
    try:
        for ip in open('rules/whiteip.txt','r').readlines():
            whitelist_ip.append(ip.strip())
        whitelist_ip = list(set(whitelist_ip))
    except Exception as e:
        print(e)

    try:
        results = Elasticsearch(es_host).search(index="%s" % index_name, body=data)
        for line in results['aggregations']['ip_count']['buckets']:
            if line['doc_count'] <= alarm_number or line['key'] in whitelist_ip:
                pass
            else:
                # get_ua(line['key'],index_name)
                alarm_data = ('%s 在 %s 内被：%s 访问： %s次') % (
                api_keyword, monitor_time, str(line['key']), str(line['doc_count']))
                print(alarm_data)
                # alarm(alarm_data)
    except Exception as e:
        alarm("es异常")

'''
加载规则
'''
def run():
    for rule in rule_file.readlines():
        try:
            api_keyword = rule.split(' ')[0]
            monitor_time = rule.split(' ')[1]
            alarm_number = int(rule.split(' ')[2])
            index_name = rule.split(' ')[3].strip()
            get_results(api_keyword,monitor_time,alarm_number,index_name)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    run()
