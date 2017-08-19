# coding: utf-8
import threading
import time
import uuid
import functools
import logging

engine = None

class _Engine(object):
    def __init__(self, connect):
        self._connect = connect
    def connect(self):
        return self._connect()

class _LasyConnection(object):
    """
    惰性连接对象
    仅当需要cursor对象时，才连接数据库，获取连接
    """
    def __init__(self):
        self.connection = None

    def cursor(self):
        if self.connection is None:
            _connection = engine.connect()
            logging.info('[CONNECTION] [POEN] connection <%s>...' % hex(id(_connection)))
            self.connection = _connection
        return self.connection.cursor()

    def commmit(self):
        self.connection.commit()

    def cleaup(self):
        if self.connection:
            _connection =self.connection
            self.connection = None
            logging.info('[CONNECTION] [CLOSE] connection <%s>...' % hex(id(_connection)))
            _connection.close()



class _DbCtx(threading.local):
    def __init__(self):
        self.connection = None
        self.transactions = 0

    def is_init(self):
        return not self.connection is None

    def init(self):
        self.connection = _LasyConnection()
        self.transactions = 0

    def cleanup(self):
        self.connection.cleanup()
        self.connection = None

    def cursor(self):
        return self.connection.cursor()

_db_ctx = _DbCtx()

class _ConnectionCtx(object):
    def __enter__(self):
        global _db_ctx
        self.should_cleanup = False
        if not  _db_ctx.is_init():
            _db_ctx.init()
            self.should_cleanup = True
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        global _db_ctx
        if self.should_cleanup:
            _db_ctx.cleanup()

class _TransactionCtx(object):
    def __enter__(self):
        global _db_ctx
        self.should_close_conn = False
        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_close_conn = True
        _db_ctx.transactions = _db_ctx.transactions + 1
        return self

    def __exit__(self, exctype, excvalue, traceback):
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
        try:
            _db_ctx.connection.commit()
        except:
            _db_ctx.connection.rollback()
            raise

    def rollback(self):
        global _db_ctx
        _db_ctx.connection.rollback()

def connection():
    return _ConnectionCtx()

def transaction():
    return _TransactionCtx()

def with_connection(func):                                  # 自定义装饰器
    @functools.wraps(func)                                  #  保留原属性的装饰器
    def _wrapper(*args,**kw):
        with _ConnectionCtx():
            return func(*args, **kw)
    return _wrapper

@with_connection
def select(sql, *args):
    pass

@with_connection
def update(sql, *args):
    pass

def _profiling(start, sql=''):
    """
    用于剖析sql的执行时间
    """
    t = time.time() - start
    if t > 0.1:
        logging.warning('[PROFILING] [DB] %s: %s' % (t, sql))
    else:
        logging.info('[PROFILING] [DB] %s: %s' % (t, sql))

def with_transaction(func):
    @functools.wraps(func)
    def _wrapper(*args,**kw):
        start = time.time()
        with _TransactionCtx(func):
            func(*args, **kw)
        _profiling(start)
    return _wrapper

@with_transaction
def do_in_transaction():
    pass




