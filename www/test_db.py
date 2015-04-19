#!/usr/bin/env python
#-*- coding:utf-8 -*-

#test_db.py
#test the db module which used to communicate with the database mySQL



from models import User,Blog,Comment
from transwarp import db

#at first you must run schema.sql to create the "awesome" database 
#and grant select, insert, update, delete on awesome.* to 'www-data'@'localhost' identified by 'www-data'; 
#just run the script use 
# $ mysql -u root -p < schema.sql
import pdb
pdb.set_trace()

db.create_engine(user='www-data',password='www-data',database ='awesome')
u = User(name = 'Test',email = 'test@example.com',password = '1234567890',image ='about:blank')
u.insert()
print 'new user id:',u.id#model中实现了__getattr__(self,key)发那个发，可以直接用u.id来取对应属性值
u1 = User.find_first('where email=?','test@example.com')
'''
	def find_first(cls,where,*args):
    	
    	Find by where clause and return one result ,if multiple results found,
    	only the first one returned ,if no result found,return None
    	
    	d = db.select_one('select * from %s %s' %(cls.__table__,where),*args)
    	return cls(**d) if d else None 
'''
print 'find user \'s name:',u1.name

u1.delet()

u2 = User.find_first('where.email = ?','test@example.com')
print 'find user:',u2 