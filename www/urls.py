#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'luodan but not original'


from transwarp.web import get, view

from models import User, Blog, Comment

@view('blogs.html')
@get('/')
def index():
    blogs = Blog.find_all()
    #查找登陆用户：
    user = User.find_first("where email=?", "danolphoenix@163.com")
    return dict(blog=blogs,user=user)
