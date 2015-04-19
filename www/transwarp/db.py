#!/usr/bin/env python
#-*- coding:utf-8 -*-

__author__ = " Rodan but not original"




''''' 设计数据库接口 以方便调用者使用  希望调用者可以通过： 

from transwarp import db 
db.create_engine(user='root',password='123456',database='test',host='127.0.0.1',port=3306) 
然后直接操作sql语句  
users=db.select('select * from user') 
返回一个list 其中包含了所有的user信息。 
其中每一个select和update等 都隐含了自动打开和关闭数据库 这样上层调用就完全不需要关心数据库底层链接 
在一个数据库中执行多条sql语句 可以用with语句实现 
with db.connection(): 
    db.select('....') 
    db.update('....') 
    db.select('....') 
同样如果在一个数据库事务中执行多个SQL语句 也可以用with实现 
with db.transactions(): 
    db.select('....') 
    db.update('....') 
    db.select('....') 
''' 

'''
Database operation module.
'''
import time,uuid,functools,threading,logging

#Dict object:
class Dict(dict):
    '''' 
    #Dict object : 重写dict 让其可以通过访问属性的方式访问对应的value  
   ---------------------------------------------以下是Dict类的定义-----------------------------------------------------
    以下是docttest.testmod()会调用作为测试的内容 也就是简单的unittest 单元测试 
    simple dict but spport access as x.y style 
 
    >>> d1 = Dict() 
    >>> d1['x'] = 100 
    >>> d1.x 
    100 
    >>> d1.y = 200 
    >>> d1['y'] 
    200 
    >>> d2 = Dict(a=1, b=2, c='3') 
    >>> d2.c 
    '3' 
    >>> d2['empty'] 
    Traceback (most recent call last): 
        ... 
    KeyError: 'empty' 
    >>> d2.empty 
    Traceback (most recent call last): 
        ... 
    AttributeError: 'Dict' object has no attribute 'empty' 
    >>> d3 = Dict(('a', 'b', 'c'), (1, 2, 3)) 
    >>> d3.a 
    1 
    >>> d3.b 
    2 
    >>> d3.c 
    3 
    @method __init__ 相当于其他语言中的构造函数 
    zip()将两个list糅合在一起 例如： 
    x=[1,2,3,4,5] 
    y=[6,7,8,9,10] 
    zip(x,y)-->就得到了[(1,6),(2,7),(3,8),(4,9),(5,10)] 
 
    ''' 
    def __init__(self, names=(), values=(), **kw):
        super(Dict,self).__init__(**kw)
        '''调用父类dict的构造方法
        继承语法 class 派生类名（基类名）：//... 基类名写作括号里，基本类是在类定义的时候，在元组之中指明的。
        class SubClassName (ParentClass1[, ParentClass2, ...]):
        在python中继承中的一些特点：
        1：在继承中基类的构造（__init__()方法）不会被自动调用，它需要在其派生类的构造中亲自专门调用。
        2：在调用基类的方法时，需要加上基类的类名前缀，且需要带上self参数变量。区别于在类中调用普通函数时并不需要带上self参数
        3：Python总是首先查找对应类型的方法，如果它不能在派生类中找到对应的方法，它才开始到基类中逐个查找。（先在本类中查找调用的方法，找不到才去基类中找）。
        '''
        for k,v in zip(names,values):
            self[k] = v
        '''
        zip()将两个list糅合在一起 例如： 
        x=[1,2,3,4,5] 
        y=[6,7,8,9,10] 
        zip(x,y)-->就得到了[(1,6),(2,7),(3,8),(4,9),(5,10)]
        '''

    '''
    @method __getattr__ 相当于新增加的get方法 
    如果对象调用的属性不存在的时候 解释器就会尝试从__getattr__()方法获得属性的值。 
    ''' 
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)




    '''
    Dict从dict继承，所以具备所有dict的功能，同时又实现了特殊方法__getattr__()和__setattr__()，所以又可以像引用普通字段那样写
    dict[id]
    dict.id
    '''
    def __setattr__(self,key,value):
        self[key] = value













'''
@method next_id() uuid4()  make a random UUID 得到一个随机的UUID 
如果没有传入参数根据系统当前时间15位和一个随机得到的UUID 填充3个0 组成一个长度为50的字符串
'''
def next_id(t = None):
    '''Return next id as 50-char string.
       Args:
           t:unix timestamp,default to None and using time.time()
    '''
    if t is None:
        t = time.time()
    return '%015d%s000' % (int(t * 1000), uuid.uuid4().hex)

'''
@method _profiling 记录sql 的运行状态  
单下划线开头的方法名或者属性 不会 from moduleName import * 中被导入 也就是说只有本模块中可以访问 
'''
def _profiling(start,sql =''):
    t = time.time() - start
    if t > 0.1:
        logging.warnning('[PROFILING][DB] %s : %s' %(t,sql))
    else:
        logging.info('[PROFILING][DB] %s : %s' %(t,sql))

class DBError(Exception):
    pass

class MultiColumnsError(DBError):
    pass


'''''对数据库连接以及最基本的操作进行了封装''' 
class _LasyConnection(object):
    def __init__(self):
        self.connection = None

    def cursor(self):#
        if self.connection is None:
            connection = engine.connect()
            #engine的_connect中保存的是一个函数:lambda:mysql.connector.connect(**params)，
            #调用engine.connect()方法时，会执行这个函数，相当于执行了真正的连接动作, 返回的结果就是指向这个数据库连接对象,赋值给connection
            logging.info('open connection <%s>...' % hex(id(connection)))
            self.connection = connection
        return self.connection.cursor()
        ''' Connection.cursor() 
        创建一个使用连接的新的Cursor对象。指针(cursor)是一个对象, 你可以使用它执行SQL查询并获得结果'''

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def cleanup(self):
        if self.connection:
            connection = self.connection
            self.connection = None
            logging.info('close connection <%s>...' % hex(id(connection)))
            connection.close()



#db.py
#database Engine Object

class _Engine(object):
    def __init__(self,connect):
        self._connect = connect
    def connect(self):
        return self._connect()

#global engine object  保存着mysql数据库的连接 
engine = None

'''
接下来解决对于不同的线程数据库链接应该是不一样的 于是创建一个变量,是一个threadlocal对象
由于_db_ctx继承threadlocal对象，所以，它持有的数据库连接对于每个线程看到的都是不一样的。任何一个线程都无法访问到其他线程持有的数据库连接
有了这engine,_db_ctx两个全局变量，我们继续实现数据库连接的上下文，目的是自动获取和释放连接
'''
engine = None

#DB Context Object
class _DbCtx(threading.local):
    '''
    thread local object that holds connection info.
    '''
    def __init__(self):
        self.connection = None
        self.transactions = 0

    def is_init(self):
        return not self.connection is None

    def init(self):
        logging.info('open lazy connection...')#打开一个数据库链接 
        self.connection = _LasyConnection()#只是初始化这样一个连接对象的形式壳子，还没有进行连接动作,_LasyConnection()对象中的.connection是None的
        self.transaction = 0

    def cleanup(self):
        self.connection.cleanup()
        self.connection = None

    def cursor(self):
        '''
        return cursor
        '''
        return self.connection.cursor()

#_db_ctx is threadlocal object, so every thread won't visit other thread's db connection.

#由于它继承threading.local 是一个threadlocal对象 所以它对于每一个线程都是不一样的。  
#所以当需要数据库连接的时候就使用它来创建 
_db_ctx = _DbCtx()
'''''=====================================以上通过_db_ctx就可以打开和关闭链接==============================================''' 

















class _Engine(object):

    def __init__(self,connect):
        #传进来的connect对象是一个函数:lambda:mysql.connector.connect(**params)
        self._connect = connect
        #将这个方法记录在_connect变量里,记录了“进行连接”的动作

    def connect(self):
        return self._connect()  
        #返回“进行连接”方法的结果
        #外界执行_Engine里的.connect方法时，执行之前初始化时保存的函数对象，相当与执行这个链接动作,
        #目测这个lambda函数返回的结果就是指向这个数据库连接的指针,拿到这个连接指针之后就可以继续对数据库进行一系列操作

#user,password，database为mySQL用户连接到mySQL所用的用户名和密码以及要操作的database
def create_engine(user,password,database,host="127.0.0.1",port = 3306,**kw):
    import mysql.connector#导入mysql模块 
    global engine #global关键字 说明这个变量在外部定义了 这是一个全局变量 
    if engine is not None:
        raise DBError('Engine is already initiallized.') #如果连接已经存在表示连接重复 则抛出一个数据库异常,
    params = dict(user=user,password=password,database=database,host=host,port=port) 
    #params保存了数据库的链接信息
    defaults = dict(use_unicode = True, charset='utf8', collation='utf8_general_ci', autocommit=False)
    #defaults保存了链接的设置 编码 等等
    for k,v in defaults.iteritems():
        #将defaults和kw中的键值对保存到params中 
        #如果有一个key两边都存在,那么保存kw的,kw是外部指定的可变参数 
        params[k] = kw.pop(k,v)
        #dict.get(key,default=None) 对字典dict中的键key,返回它对应的值value，如果字典中不存在此键，则返回default 的值(注意，参数default 的默认值为None)
        #dict.pop(key[, default]) 和方法get()相似，如果字典中key 键存在，删除并返回dict[key]，如果key 键不存在，且没有给出default 的值，引发KeyError 异常。
        #kw.pop(k,v),k是要在kw中查找的键值,v相当于是默认值，这个默认值是从defaults中取出来的，
        #如果kw中有k这个键值，那么就返回kw中k对应键值的value值，如果kw中没有k键值，那么就返回默认值，默认值就是defaults中的k对应的v值
    params.update(kw)
    #dict.update(dict2),update()函数把字典dict2的键/值对更新到dict里.若是dict1中已经有的键值，用dict2中的覆盖
    #如果kw中还有其他参数，都装进params中
    params['buffered'] = True
    import pdb
    pdb.set_trace()
    engine = _Engine(lambda:mysql.connector.connect(**params))
    #在这里(lambda:mysql.connector.connect(**params))返回的是一个函数而不是一个connection对象
    #注意engine是在下面用_Engine创建的用当前传入的params标识的链接engine 
    #engine持有了一个可以执行连接动作的函数，相当于保存一个动作
    logging.info('Init mysql engine<%s> ok.' %hex(id(engine)))
    #id函数可以获得对象的内存地址

'''''===================以上通过engine这个全局变量就可以获得一个数据库链接，重复链接抛异常============================='''

#Automatically acquire and release connection.if you wanna to do some db operation,can use WITH sentence or @,then everytime do db operation,it will acquire and release db connection automatically.
#通过with语句让数据库链接可以自动创建和关闭  
''''' 
 with 语句： 
 with 后面的语句会返回 _ConnectionCtx 对象 然后调用这个对象的 __enter__方法得到返回值 返回值赋值给as后面的变量 然后执行 
 with下面的语句 执行完毕后 调用那个对象的 __exit__()方法 
'''  

#Automatically acquire and release connection.if you wanna to do some db operation,can use WITH sentence or @,then everytime do db operation,it will acquire and release db connection automatically.
class _ConnectionCtx(object):
    '''
    _ConnectionCtx object that can open and close connection context. _ConnectionCtx object can be nested and only the most
    outer connection has effect.
    with connection():
        pass
        with connection():
            pass
    '''
    def __enter__(self):
        #use 'global' to tell python the variable _db_ctx is defined out of this func
        import pdb
        pdb.set_trace()
        global _db_ctx
        self.should_cleanup = False
        if not _db_ctx.is_init():#是否_db_ctx.connection被初始化为连接对象LazyConnection
            _db_ctx.init()#初始化了_db_ctx.connection为连接外壳LazyConnection对象，不再为none,transaction为0,但是还没有进行真正的连接动作
            self.should_cleanup = True
        return self

    def __exit__(self,exctype,excvalue,traceback):
        import pdb
        pdb.set_trace()
        global _db_ctx
        if self.should_cleanup:
            _db_ctx.cleanup()

def connection():
    '''
    return _ConnectionCtx object that can be used by "with" statement:

    with connection():
        pass
    '''
    return _ConnectionCtx()


#采用装饰器的方法 让其能够进行共用同一个数据库连接
def with_connection(func):
    '''
    Decorator for reuse connection.
    @with_connection
    def foo(*args,**kw):
        f1()
        f2()
    '''
    @functools.wraps(func)
    def _wrapper(*args,**kw):
        with _ConnectionCtx():#_enter_初始化了_db_ctx.connection为LazyConnection，transaction为0，还没有执行连接动作
            return func(*args,**kw)
    return _wrapper


class _TransactionCtx(object):
    '''_TransactionCtx object that can handle transactions.

    with _TransactionCtx():
        pass
    '''

    def __enter__(self):
        global _db_ctx
        self.should_close_conn = False
        if not _db_ctx.is_init():#是否有连接,
            #needs open a connection first:
            _db_ctx.init()
            self.should_close_conn = True
        _db_ctx.transactions = _db_ctx.transactions + 1
        logging.info('begin transaction...'if _db_ctx.transactions == 1 else 'join current transaction...')
        return self

    def __exit__(self, exctype,excvalue,traceback):
        global _db_ctx
        _db_ctx.transactions = _db_ctx.transactions - 1
        try:
            if _db_ctx.transactions==0:
                if exctype is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            if self.should_close_conn:
                _db_ctx.cleanup()

    def commit(self):
        global _db_ctx
        logging.info('commit transaction...')
        try:
            _db_ctx.connection.commit()
            logging.info('commit ok.')
        except:
            logging.warning('commit failed,try rollback...')
            _db_ctx.connection.rollback()
            logging.info('rollback ok.')
            raise

    def rollback(self):
        global _db_ctx
        logging.info('rollback transaction...')
        _db_ctx.connection.rollback()
        logging.info('rollback ok')

def transaction():
    '''
    create a transaction object so can use with statement:

    with transaction():
        pass

    Create a transaction object so can use with statement:
    with transaction():
    pass
    >>> def update_profile(id, name, rollback):
    ... u = dict(id=id, name=name, email='%s@test.org' % name, passwd=name, last_modified=time.time())
    ... insert('user', **u)
    ... r = update('update user set passwd=? where id=?', name.upper(), id)
    ... if rollback:
    ... raise StandardError('will cause rollback...')
    >>> with transaction():
    ... update_profile(900301, 'Python', False)
    >>> select_one('select * from user where id=?', 900301).name
    u'Python'
    >>> with transaction():
    ... update_profile(900302, 'Ruby', True)
    Traceback (most recent call last):
    ...
    StandardError: will cause rollback...
    >>> select('select * from user where id=?', 900302)
    []
    '''
    return _TransactionCtx()

def with_transaction(func):
    '''
     A decorator that makes function around transaction.
     >>> @with_transaction
    ... def update_profile(id, name, rollback):
    ... u = dict(id=id, name=name, email='%s@test.org' % name, passwd=name, last_modified=time.time())
    ... insert('user', **u)
    ... r = update('update user set passwd=? where id=?', name.upper(), id)
    ... if rollback:
    ... raise StandardError('will cause rollback...')
    >>> update_profile(8080, 'Julia', False)
    >>> select_one('select * from user where id=?', 8080).passwd
    u'JULIA'
    >>> update_profile(9090, 'Robert', True)
    Traceback (most recent call last):
    ...
    StandardError: will cause rollback...
    >>> select('select * from user where id=?', 9090)
    []
    ''' 
    @functools.wraps(func)
    def _wrapper(*args,**kw):
        _start = time.time()
        with _TransactionCtx():
            return func(args,**kw)
        _profiling(start)
    return _wrapper


def _select(sql,first,*args):
    '''
    execute select SQL and return unique result or list results
    '''
    global _db_ctx
    cursor = None
    sql = sql.replace('?','%s')
    logging.info('SQL:%s,ARGS:%s' % (sql,args))
    try:
        cursor = _db_ctx.connection.cursor()
        '''创建一个使用连接的新的Cursor对象。指针(cursor)是一个对象, 你可以使用它执行SQL查询并获得结果'''
        cursor.execute(sql,args)
        '''do the operation described by sql and args like this
        #写入    
        sql = "insert into user(name,created) values(%s,%s)"   
        param = ("aaa",int(time.time()))    
        n = cursor.execute(sql,param) 
        '''
        if cursor.description:
            '''.description得到域的名字'''
            names = [x[0] for x in cursor.description]
        if first:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(names,values)
        return [Dict(names,x) for x in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()

@with_connection
def select_one(sql,*args):
    '''
    Execute select SQL and expected one result.
    If no result found, return None.
    If multiple results found, the first one returned.
    >>> u1 = dict(id=100, name='Alice', email='alice@test.org', passwd='ABC-12345', last_modified=time.time())
    >>> u2 = dict(id=101, name='Sarah', email='sarah@test.org', passwd='ABC-12345', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> insert('user', **u2)
    1
    >>> u = select_one('select * from user where id=?', 100)
    >>> u.name
    u'Alice'
    >>> select_one('select * from user where email=?', 'abc@email.com')
    >>> u2 = select_one('select * from user where passwd=? order by email', 'ABC-12345')
    >>> u2.name
    u'Alice'
    '''
    return _select(sql,True,*args)

@with_connection
def select_int(sql,*args):
    ''''' 
    Execute select SQL and expected one int and only one int result.  
 
    >>> n = update('delete from user') 
    >>> u1 = dict(id=96900, name='Ada', email='ada@test.org', passwd='A-12345', last_modified=time.time()) 
    >>> u2 = dict(id=96901, name='Adam', email='adam@test.org', passwd='A-12345', last_modified=time.time()) 
    >>> insert('user', **u1) 
    1 
    >>> insert('user', **u2) 
    1 
    >>> select_int('select count(*) from user') 
    2 
    >>> select_int('select count(*) from user where email=?', 'ada@test.org') 
    1 
    >>> select_int('select count(*) from user where email=?', 'notexist@test.org') 
    0 
    >>> select_int('select id from user where email=?', 'ada@test.org') 
    96900 
    >>> select_int('select id, name from user where email=?', 'ada@test.org') 
    Traceback (most recent call last): 
        ... 
    MultiColumnsError: Expect only one column. 
    ''' 
    d = _select(sql,True,*args)
    if len(d) != 1:
        '''WHY??? TO ASK BROTHER TIAN'''
        raise MultiColumnsError('Expect only one column.')
    return d.values()[0]

@with_connection
def select(sql,*args):
    '''
    Execute select SQL and return list or empty list if no result.
    >>> u1 = dict(id=200, name='Wall.E', email='wall.e@test.org', passwd='back-to-earth', last_modified=time.time())
    >>> u2 = dict(id=201, name='Eva', email='eva@test.org', passwd='back-to-earth', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> insert('user', **u2)
    1
    >>> L = select('select * from user where id=?', 900900900)
    >>> L
    []
    >>> L = select('select * from user where id=?', 200)
    >>> L[0].email
    u'wall.e@test.org'
    >>> L = select('select * from user where passwd=? order by id desc', 'back-to-earth')
    >>> L[0].name
    u'Eva'
    >>> L[1].name
    u'Wall.E'
    '''
    return _select(sql, False, *args)

@with_connection
def _update(sql,*args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?','%s')
    logging.info('SQL:%s,ARGS:%s' %(sql,args))
    try:
        import pdb
        pdb.set_trace
        cursor = _db_ctx.connection.cursor()
        #在with_connection的_enter_里只是指定了 _db_ctx.connection为LazyConnection对象，
        #但是还没有执行真正的连接动作，在LazyConnection.connection中是None
        #用之前初始化的engine参数params获取一个真实的连接
        #如果连接参数错误，会抛异常*** OperationalError: OperationalError()
        cursor.execute(sql,args)#执行传入的sql语句
        r = cursor.rowcount
        if _db_ctx.transactions == 0:
            #no transaction environment:
            logging.info('auto commit')
            _db_ctx.connection.commit()
        return r
    finally:
        if cursor:#如果之前的连接不成功，那么这里的cursor是none
            cursor.close()

def insert(table,**kw):
    '''
    Execute insert SQL.
    >>> u1 = dict(id=2000, name='Bob', email='bob@test.org', passwd='bobobob', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> u2 = select_one('select * from user where id=?', 2000)
    >>> u2.name
    u'Bob'
    >>> insert('user', **u2)
    Traceback (most recent call last):
    ...
    IntegrityError: 1062 (23000): Duplicate entry '2000' for key 'PRIMARY'
    '''
    cols,args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)

def update(sql,*args):
    r''' 
    Execute update SQL.
    >>> u1 = dict(id=1000, name='Michael', email='michael@test.org', passwd='123456', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> u2 = select_one('select * from user where id=?', 1000)
    >>> u2.email
    u'michael@test.org'
    >>> u2.passwd
    u'123456'
    >>> update('update user set email=?, passwd=? where id=?', 'michael@example.org', '654321', 1000)
    1
    >>> u3 = select_one('select * from user where id=?', 1000)
    >>> u3.email
    u'michael@example.org'
    >>> u3.passwd
    u'654321'
    >>> update('update user set passwd=? where id=?', '***', '123\' or id=\'456')
    0
    '''
    return _update(sql, *args)

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    import pdb
    pdb.set_trace()
 
    create_engine('luodan', 'a', 'webapp')
  #Dict()  
    #create_engine('root','123456','pythonstudy')  
    #print engine.connect()  
    #create_engine('root','123456','pythonstudy')  
    '''
    import threading 
    d1=threading.Thread(target=_db_ctx.init) 
    d2=threading.Thread(target=_db_ctx.init) 
    d1.start() 
    d2.start() 
    d1.join() 
    d2.join() 
    这样测试可以看到每一个线程的数据库连接的id都不是一样的 可以知道每一个线程拥有不同的数据库链接 
    '''

    ''' 
    with transaction(): 
        print 'dd' 
        u1=dict(id=900301,name='python',email='python@test.org' ,passwd='python',last_modified=time.time()) 
        insert('user',**u1) 
        print 'hellp' 
    '''  
    create_engine('root', 'a', 'webapp')
 
    update('drop table if exists user')
    update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    import doctest
    doctest.testmod()




