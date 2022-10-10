# encoding: utf-8
'''
Author: Eva
'''
import base64
import sys
import json
import pymysql.cursors
import urllib
import requests
import telnetlib
import os
import urllib3
from datetime import datetime
from mountains.file.excel import write_excel, read_excel
from mountains.datetime.converter import datetime2str
from atexit import register
from time import ctime
from random import randint
from threading import BoundedSemaphore, Semaphore, Lock, Thread

        
# 需要配置fofa和数据库后使用

reload(sys)
sys.setdefaultencoding('utf-8')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FOFA_EMAIL = 'xx.com'    
FOFA_KEY = 'xx'


class Client(object):
    def __init__(self, email=FOFA_EMAIL, key=FOFA_KEY):
        self.email = email
        self.key = key
        self.base_url = "https://fofa.so"
        self.search_api_url = "/api/v1/search/all"
        self.login_api_url = "/api/v1/info/my"
        self.get_userinfo()  # check email and key

    def get_userinfo(self):
        api_full_url = "%s%s" % (self.base_url, self.login_api_url)
        params = {"email": self.email, "key": self.key}
        res = requests.get(api_full_url, params=params)
        return res.json()

    def get_data(self, query_str, page=1, fields=""):
        res = self.get_json_data(query_str, page, fields)
        return res

    def get_json_data(self, query_str, page=1, size=100, fields=""):
        api_full_url = "%s%s" % (self.base_url, self.search_api_url)
        # print( base64.b64encode(query_str))
        # print(query_str.encode())
        params = {
            "qbase64": base64.b64encode(query_str),
            "email": self.email,
            "key": self.key,
            "page": page,
            "size": size,
            "fields": fields
        }
        res = self.http_get(api_full_url, params)
        return res

    def http_get(self, url, params):
        retry_index = 3
        while retry_index > 0:
            try:
                req = requests.get(url, params=params)
                # print(req.text)
                res = req.json()
                if res.get('error') is False:
                    return res
                else:
                    print("errmsg：{}".format(res.get('errmsg')))
            except Exception as e:
                print("errmsg：{}".format(e))

            retry_index -= 1

        return None


class Scanner(object):
    def __init__(self, project_name, query_str):
        self.project_name = project_name
        self.query_str = query_str
        self.data_path = 'data/' + self.project_name
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    def query(self, max_count=10000):
        client = Client()
        query_str = self.query_str
        fields = [
            "host",
            "title",
            "ip",
            "domain",
            "port",
            "city",
            # "header",
            "server",
            "protocol",
            "banner",
            # "cert",
            # "isp",
            # "as_number",
            "as_organization",
            "country"
        ]

        data = []
        page = 1
        while True:
            r = client.get_json_data(
                query_str, page=page, size=10000, fields=','.join(fields))
            if r is not None:
                results = r.get('results')
                size = r.get('size')
                if page == 1:
                    print(size)
                    # print(results)
                print(len(results))
                data.extend(results)
                # print(page)
                if len(results) <= 0:
                    break
            if len(data) >= max_count:
                break
            page += 1
        with open(os.path.join(self.data_path, 'result.json'), 'w') as f:
            f.write(json.dumps(data))

    def to_excel(self):
        with open(os.path.join(self.data_path, 'result.json'), 'r') as f:
            data = f.read()

        fields = [
            "host",
            "title",
            "ip",
            "domain",
            "port",
            "city",
            # "header",
            "server",
            "protocol",
            "banner",
            # "cert",
            # "isp",
            # "as_number",
            "as_organization",
            "country"
        ]
        data = json.loads(data)
        for row in data:
            row = {fields[i]: c for i, c in enumerate(row)}

        write_excel(fields, data, os.path.join(
            self.data_path, 'result.xlsx'))


class Source(object):
    def __init__(self, city_code):
        self.city_code = city_code

    def city(self):
        str_pol = []
        conn = pymysql.connect(
            host='',
            user='',
            passwd='',
            db='',
            charset='utf8'
        )
        cursor = conn.cursor()

        sql_select_student = "select short_name from cnarea_2019 where city_code = " + \
            self.city_code + " and level <= 2;"
        
        cursor.execute(sql_select_student)
        
        for i in cursor.fetchall():
            str_pol.append(i[0]+'移动')

        str_pol.append('移动')
        conn.commit()  # 提交，不然无法保存插入或修改的数据
        cursor.close()  # 关闭游标
        conn.close()  # 关闭连接
        
        str_pol = list(set(str_pol))
        
        return str_pol


class main():
    
    # s = Source("0591")
    # for x in s.city():
    #     print(json.dumps(x).decode("unicode-escape"))
    
    for j in range(1, 10, 1):
        s = Source("059"+str(j))
        for i in s.city():
            #name = json.dumps(i).decode("unicode-escape")
            project_name = "059"+str(j)+'/'+i
            query_str = "title= '"+i+"' || body = '"+ i +"'"
            s = Scanner(project_name,query_str)
            s.query()
            s.to_excel()
        

    # name = print(json.dumps(i).decode("unicode-escape"))
    # project_name = name
    # query_str = "title= '"+name+" 移动' || body = '"+ name +"'"
    # s = Scanner(project_name, query_str)
    # s.query()
    # s.to_excel()

    pass


if __name__ == "__main__":

    main()
