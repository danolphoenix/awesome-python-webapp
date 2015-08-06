#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'rodan but not original'

'''
A WSGI application entry.
'''

import logging; logging.basicConfig(level=logging.INFO)

import os

from transwarp import db
from transwarp.web import WSGIApplication, Jinja2TemplateEngine

from config import configs

# init db:
print configs.db
print configs.db['user']
print configs.db['password']
print configs.db['database']

import pdb
pdb.set_trace()

db.create_engine(configs.db['user'],configs.db['password'],configs.db['database'])#,**configs.db)

# init wsgi app:
wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

wsgi.template_engine = template_engine

import urls

wsgi.add_module(urls)

if __name__ == '__main__':
	import pdb
	pdb.set_trace()
	wsgi.run(9000)

