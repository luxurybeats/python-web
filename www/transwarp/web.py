# -*- coding: utf-8 -*-
"""
这是一个简单的， 轻量级的， WSGI兼容(Web Server Gateway Interface)的web 框架
WSGI概要：
    工作方式： WSGI server -----> WSGI 处理函数
    作用：将HTTP原始的请求、解析、响应 这些交给WSGI server 完成，
          让我们专心用Python编写Web业务，也就是 WSGI 处理函数
          所以WSGI 是HTTP的一种高级封装。
    例子：
        wsgi 处理函数
            def application(environ, start_response):
                method = environ['REQUEST_METHOD']
                path = environ['PATH_INFO']
                if method=='GET' and path=='/':
                return handle_home(environ, start_response)
                if method=='POST' and path='/signin':
                return handle_signin(environ, start_response)
        wsgi server
            def run(self, port=9000, host='127.0.0.1'):
                from wsgiref.simple_server import make_server
                server = make_server(host, port, application)
                server.serve_forever()
设计web框架的原因：
    1. WSGI提供的接口虽然比HTTP接口高级了不少，但和Web App的处理逻辑比，还是比较低级，
       我们需要在WSGI接口之上能进一步抽象，让我们专注于用一个函数处理一个URL，
       至于URL到函数的映射，就交给Web框架来做。
设计web框架接口：
    1. URL路由： 用于URL 到 处理函数的映射
    2. URL拦截： 用于根据URL做权限检测
    3. 视图： 用于HTML页面生成
    4. 数据模型： 用于抽取数据（见models模块）
    5. 事物数据：request数据和response数据的封装（thread local）

"""
import types, os, re, cgi, sys, time, datetime, functools, mimetypes, threading, logging, traceback, urllib
from db import Dict

ctx = threading.local()     # 全局ThreadLocal对象

class HttpError(Exception):
    """
    HTTP错误类
    """
    pass

class Request(object):
    """
    request对象
    """
    def get(self, key, default=None):
        """
        根据key返回value
        :param key:
        :param default:
        :return:
        """
        pass

    def input(self):
        """
        返回key-value 的dict
        :return:
        """
        pass

    @property
    def path_info(self):
        """
        返回URL的path
        :return:
        """
        pass

    @property
    def headers(self):
        """
        返回HTTP Hearders
        :return:
        """
        pass

    def cookie(self, name, default=None):
        """
        根据key 返回Cookie value
        :param name:
        :param default:
        :return:
        """
        pass

class Response(object):
    """
    response 对象
    """
    def set_header(self, key, value):
        """
        设置header
        :param key:
        :param value:
        :return:
        """
        pass

    def set_cookie(self, name, value, max_age=None, expires=None, path='/'):
        """
        设置Cookie
        :param name:
        :param value:
        :param max_age:
        :param expires:
        :param path:
        :return:
        """
        pass

    @property
    def status(self):
        """
        设置status
        :return:
        """
        pass

    @status.setter
    def status(self, value):
        pass

def get(path):
    """
    定义GET
    :param path:
    :return:
    """
    pass

def post(path):
    """
    定义POST
    :param path:
    :return:
    """
    pass

def view(path):
    """
    定义模板
    :param path:
    :return:
    """
    pass

def interceptor(pattern):
    """
    定义拦截器
    :param pattern:
    :return:
    """
    pass

class TemplateEngine(object):
    """
    定义末班引擎
    """
    def __call__(self, path, model):
        pass

class Jinja2TemplateEngine(TemplateEngine):
    """
    渲染使用jinja2模板引擎
    """
    def __init__(self, templ_dir, **kw):
        from jinja2 import Environment, FileSystemLoader
        self._env = Environment(loader=FileSystemLoader(templ_dir), **kw)

    def __call__(self, path, model):
        return self._env.get_template(path).render(**model).encode('utf-8')

class WSGIApplication(object):
    """

    """
    def __init__(self, document_root=None, **kw):
        pass

    def add_url(self,func):
        """
        添加一个URL定义
        :param func:
        :return:
        """
        pass

    def add_interceptor(self, func):
        """
        添加一个Interceptor定义
        :param func:
        :return:
        """
        pass

    @property
    def template_engine(self):
        """
        设置TemplateEngine
        :return:
        """
        pass

    @template_engine.setter
    def template_engine(self, engine):
        pass

    def get_wsgi_application(self):
        """
        返回WSGI处理函数
        :return:
        """
        def wsgi(env, start_response):
            pass
        return wsgi

    def run(self, port=9000, host='127.0.0.1'):
        from wsgiref.simple_server import make_server
        server = make_server(host, port, self.get_wsgi_application())
        server.server_forever()






























































