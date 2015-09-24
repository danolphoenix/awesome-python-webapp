#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'rodan but not original'

'''
A WSGI application entry.
'''

import logging; logging.basicConfig(level=logging.INFO)

import os,time
from datetime import datetime

from transwarp import db
from transwarp.web import WSGIApplication, Jinja2TemplateEngine

from config import configs

# init db:
print configs.db
print configs.db['user']
print configs.db['password']
print configs.db['database']


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


db.create_engine(configs.db['user'],configs.db['password'],configs.db['database'],configs.db['host'])#,**configs.db)

# init wsgi app:
wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
template_engine.add_filter('datetime',datetime_filter)

wsgi.template_engine = template_engine

import urls

wsgi.add_interceptor(urls.user_interceptor)
wsgi.add_interceptor(urls.manage_interceptor)
wsgi.add_module(urls)
# add_module(urls)会检查urls这个模块里所有的属性对象，如果该属性对象是callable且有__web_route__和__web_method__属性（通常是被get和post装饰过），
# 就用使用该方法作为入参建立一个Route对象，判断它的path（方法的__web_route__）是不是静态的，非静态路由会比静态路由多一个self.route属性，里面包含了适配范围。
# 创建好Route对象之后，会把它放到这个wsgiApplication的路由记录表里,所有被get，post装饰器装饰过的方法都会被登记起来


if __name__ == '__main__':

	wsgi.run(9000)
else:
    application = wsgi.get_wsgi_application()
