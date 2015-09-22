#!/usr/bin/env python
#-*- coding:utf-8 -*-

__author__ = 'Rodan but not original'
'''
Database operation module. This module is independent with web module.
'''

import time,logging

import db

class Field(object):
    _count = 0

    def __init__(self,**kw):
        #name:数据项的名字
        self.name = kw.get('name', None)
        self._default = kw.get('default', None)
        #primary_key:固定优先查询项，如依靠id来进行查询，那么id必须是不可变且非空的，并且一个实体只能有一个id值
        self.primary_key = kw.get('primary_key', False)
        #nullable:该数据想是否可以为空
        self.nullable = kw.get('nullable', False)
        #updatable：该数据项是否可以更改
        self.updatable = kw.get('updatable', True)
        #insertable：该数据项是否可以插入。。什么鬼
        self.insertable = kw.get('insertable', True)
        #ddl:数据类型？
        self.ddl = kw.get('ddl', '')
        self._order = Field._count
        Field._count = Field._count + 1

    #对于类的方法，装饰器一样起作用。@property装饰器就是负责把一个方法变成属性调用的
    #把一个getter方法function(self)变成属性，只需要加上@property就可以了
    #此时，@property本身又创建了另一个装饰器@function.setter，负责把一个setter方法function(self,value)变成属性赋值
    @property
    def default(self):
    	d = self._default
    	return d() if callable(d) else d
    	#callable(object)
        #中文说明：检查对象object是否可调用。如果返回True，object仍然可能调用失败；但如果返回False，调用对象ojbect绝对不会成功。
        #注意：类是可调用的，而类的实例实现了__call__()方法才可调用。

    def __str__(self):
    	s = ['<%s:%s,%s,default(%s),'% (self.__class__.__name__,self.name,self.ddl,self._default)]
        self.nullable and s.append('N')
        self.updatable and s.append('U')
        self.insertable and s.append('I')
        s.append('>')
        return ''.join(s)

class StringField(Field):

	def __init__(self,**kw):
		if not 'default' in kw:
			kw['default'] = ''
		if not 'ddl' in kw:
			kw['ddl'] = 'varchar(255)'
		super(StringField,self).__init__(**kw)

class IntegerField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'ddl' in kw:
            kw['ddl'] = 'bigint'
        super(IntegerField, self).__init__(**kw)

class FloatField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
        	kw['default'] = 0.0
        if not 'ddl' in kw:
            kw['ddl'] = 'real'
        super(FloatField, self).__init__(**kw)

class BooleanField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = False
		if not 'ddl' in kw:
			kw['ddl'] = 'bool'
		super(BooleanField, self).__init__(**kw)

class TextField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = ''
		if not 'ddl' in kw:
			kw['ddl'] = 'text'
		super(TextField, self).__init__(**kw)

class BlobField(Field):
	def __init__(self, **kw):
		if not 'default' in kw:
			kw['default'] = ''
		if not 'ddl' in kw:
			kw['ddl'] = 'blob'
		super(BlobField, self).__init__(**kw)

class VersionField(Field):
	def __init__(self, name = None):
		super(VersionField, self).__init__(name=name, default=0, ddl='bigint')

_triggers = frozenset(['pre_insert','pre_update','pre_delete'])
#set有两种类型，set和frozenset。
#set是可变的，有add（），remove（）等方法。既然是可变的，所以它不存在哈希值。
#frozenset是冻结的集合，它是不可变的，存在哈希值，好处是它可以作为字典的key，也可以作为其它集合的元素。缺点是一旦创建便不能更改，没有add，remove方法。


#传入参数包括有：表的名字table_name，表中所有的数据项目mappings
#将数据项目（如user表的id，name，email，passwd），固定有限查询项目primary_key等都填充到sql语句中，最后形成一个创建新表的sql语句
def _gen_sql(table_name, mappings):
    pk = None
    sql = ['-- generating SQL for %s:' % table_name, 'create table `%s` (' % table_name]
    for f in sorted(mappings.values(), lambda x, y: cmp(x._order, y._order)):
        if not hasattr(f, 'ddl'):
            raise StandardError('no ddl in field "%s".' % n)
        ddl = f.ddl
        nullable = f.nullable
        if f.primary_key:
            pk = f.name
        sql.append(nullable and ' `%s` %s,' % (f.name, ddl) or ' `%s` %s not null,' % (f.name, ddl))
    sql.append(' primary key(`%s`)' % pk)
    sql.append(');')
    return '\n'.join(sql)


#ModelMetaclass元类，用于创建和sql表相对应的模型类，如和User表对应的User类
class ModelMetaclass(type):
    '''
	ModelMetaclass for model class
	'''
    #skip base Model Class
    def __new__(cls,name,bases,attrs):
        if name == 'Model':
            return type.__new__(cls,name,bases,attrs)

        #store all subclasses info:
        #凡是由cls定义出来的类，那么肯定记录在cls的sublclasses表中，如果已经存在对应项，表示该类已经定义过了
        #不是父类和子类的关系，而是元类和经由元类定义的类的关系
        if not hasattr(cls, 'subclasses'):
        	cls.subclasses = {}
        if not name in cls.subclasses:
        	cls.subclasses[name] =  name
        else:
        	logging.warnning('Redifine class:%s' %name)

        logging.info('Scan ORMapping %s...' %name)
        mappings = dict()
        primary_key = None
        for k,v in attrs.iteritems():
            if isinstance(v,Field):
                if not v.name:
        			v.name = k
                logging.info('Found mapping: %s => %s' % (k, v))
        		#check duplicat primary key:
        		#primary_key:固定优先查询项，如依靠id来进行查询，那么id必须是不可变且非空的，并且一个实体只能有一个id值
                if v.primary_key:
        			if primary_key:
        				raise TypeError('Cannot define more than 1 primary key in class:%s'%name)
        			if v.updatable:
        				logging.warning('Note:change primary key to non-updatable')
        				v.updatable = False
        			if v.nullable:
        				logging.warning('Note:change primary key to non-nullable.')
        				v.nullable = False
        			primary_key = v
                mappings[k] = v
         # check exist of primary key:
        if not primary_key:
            raise TypeError('Primary key not defined in class: %s' % name)
        for k in mappings.iterkeys():
        	attrs.pop(k)
        if not '__table__'in attrs:
        	attrs['__table__'] = name.lower()
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] =  primary_key

        attrs['__sql__'] = lambda self:_gen_sql(attrs['__table__'],mappings)
        #用于生成对应的表，传入参数包含表名字attrs['__table__']，和表中每一行包含的数据项目mappings
        for trigger in _triggers:
        	if not trigger in attrs:
        		attrs[trigger] = None
        return type.__new__(cls,name,bases,attrs)





class Model(dict):
    '''
    Model从dict继承，所以具备所有dict的功能，同时又实现了特殊方法__getattr__()和__setattr__()，所以又可以像引用普通字段那样写：
    >>> user['id']
    123
    >>> user.id
    123
    '''
    '''
    Base class for ORM.
    >>> class User(Model):
    ... id = IntegerField(primary_key=True)
    ... name = StringField()
    ... email = StringField(updatable=False)
    ... passwd = StringField(default=lambda: '******')
    ... last_modified = FloatField()
    ... def pre_insert(self):
    ... self.last_modified = time.time()
    >>> u = User(id=10190, name='Michael', email='orm@db.org')
    >>> r = u.insert()
    >>> u.email
    'orm@db.org'
    >>> u.passwd
    '******'
    >>> u.last_modified > (time.time() - 2)
    True
    >>> f = User.get(10190)
    >>> f.name
    u'Michael'
    >>> f.email
    u'orm@db.org'
    >>> f.email = 'changed@db.org'
    >>> r = f.update() # change email but email is non-updatable!
    >>> len(User.find_all())
    1
    >>> g = User.get(10190)
    >>> g.email
    u'orm@db.org'
    >>> r = g.delete()
    >>> len(db.select('select * from user where id=10190'))
    0
    >>> import json
    >>> print User().__sql__()
    -- generating SQL for user:
    create table `user` (
    `id` bigint not null,
    `name` varchar(255) not null,
    `email` varchar(255) not null,
    `passwd` varchar(255) not null,
    `last_modified` real not null,
    primary key(`id`)
    );
    '''
    __metaclass__ = ModelMetaclass

    def __init__(self,**kw):
        super(Model,self).__init__(**kw)

    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribte '%s'"% key)

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    # 一般方法使用 类生成的对象调用,静态方法用类直接调用,类方法用类直接调用类当参数传入方法
    #对于classmethod的参数，需要隐式地传递类名，而staticmethod参数中则不需要传递类名，其实这就是二者最大的区别。
    #@classmethod 仅仅适用于单独的，与类本身的数据结构无关函数，其实用了它的函数，与使用普通函数无异，甚至不能在参数里加入 self，如果要在其中使用类的数据结构，仍然需要将类实例化一次才可以，所以要小心使用。
    #get这个方法和find_first的区别在于，get方法只支持使用primary_key作为查询关键字
    def get(cls,pk):#这里的cls是类名,u = User.get('123')可以直接返回一个User类实例给u
       '''Get by primary key'''
       d = db.select_one('select * from %s where %s =?' % (cls.__table__,cls.__primary_key__.name),pk)
       return cls(**d) if d else None


    #find_first支持任意字段值查询，但是返回满足条件的第一个
    @classmethod
    def find_first(cls,where,*args):
    	'''
    	Find by where clause and return one result ,if multiple results found,
    	only the first one returned ,if no result found,return None
    	'''
    	d = db.select_one('select * from %s %s' %(cls.__table__,where),*args)
    	return cls(**d) if d else None

    #find_all返回整张表里所有的值，组装成一个对象实例列表返回
    @classmethod
    def find_all(cls,*args):
    	'''
    	Find all and return list.
    	'''
    	L = db.select('select * from `%s`' % cls.__table__)
    	return [cls(**d) for d in L]

    #find_by支持任意字段值查询，返回满足条件的所有值
    @classmethod
    def find_by(cls,where,*args):
        '''
        Find by where clause and return list.
        '''
        L = db.select('select * from `%s` %s' % (cls.__table__, where), *args)
        return [cls(**d) for d in L]

    #count_all查出某表__primary_key__字段的集合，也就是有几条记录
    @classmethod
    def count_all(cls):
    	'''
    	Find by  'select count(pk) from table' and return integar.
    	'''
    	return db.select_int('select count (`%s`) from `%s`' % (cls.__primary_key__,cls.__table__))

    #count_by查出某表中满足where=args的记录条数
    @classmethod
    def count_by(cls,where,*args):
        '''
        find by 'select count(pk) from table where ...' and return int.
        '''
        return db.select_int('select count (`%s`) from `%s` %s '% (cls.__primary_key__.name, cls.__table__, where), *args)

    def update(self):
    	self.pre_update and self.pre_update()#where are these two functions from?
    	L = []
    	args = []
    	for k,v in self.__mappings__.iteritems():
    		if v.updatable:
    			if hasattr(self,k):
    				arg = getattr(self,k)
    			else:
    				arg = v.default
    				setattr(self,k,arg)
    			L.append('`%s` = ?' % k)
    			args.append(arg)
    	pk = self.__primary_key__.name
    	args.append(getattr(self,pk))
    	db.update('update `%s` set %s where %s=?' % (self.__table__,','.join(L),pk),*args)
    	return self

    def delete(self):
    	self.pre_delete and self.pre_delete()
    	pk = self.__primary_key__.name
    	args = (getattr(self,pk),)
    	db.update('delete from `%s` where `%s` =?' % (self.__table__,pk),*args)
    	return self

    #构造了某对象instance,instance.insert(),则将instance自动插入到该对象类的表中
    def insert(self):
    	self.pre_insert and self.pre_insert()
    	params = {}
    	for k,v in self.__mappings__.iteritems():
    		if v.insertable:
    			if not hasattr(self,k):
    				setattr(self,k,v.default)
    			params[v.name] = getattr(self,k)
    	db.insert('%s' % self.__table__,**params)
    	return self

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    db.create_engine('www-data', 'www-data', 'test')
    db.update('drop table if exists user')
    db.update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    import doctest
    doctest.testmod()



