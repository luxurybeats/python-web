# -*- coding: utf-8 -*-
"""
orm模块设计的原因：
    1. 简化操作
        sql操作的数据是 关系型数据， 而python操作的是对象，为了简化编程 所以需要对他们进行映射
        映射关系为：
            表 ==>  类
            行 ==> 实例
设计orm接口：
    1. 设计原则：
        根据上层调用者设计简单易用的API接口
    2. 设计调用接口
        1. 表 <==> 类
            通过类的属性 来映射表的属性（表名，字段名， 字段属性）
                from transwarp.orm import Model, StringField, IntegerField
                class User(Model):
                    __table__ = 'users'
                    id = IntegerField(primary_key=True)
                    name = StringField()
            从中可以看出 __table__ 拥有映射表名， id/name 用于映射 字段对象（字段名 和 字段属性）
        2. 行 <==> 实例
            通过实例的属性 来映射 行的值
                # 创建实例:
                user = User(id=123, name='Michael')
                # 存入数据库:
                user.insert()
            最后 id/name 要变成 user实例的属性

"""

import db
import time
import logging


_triggers = frozenset(['pre_insert', 'pre_update', 'pre_delete'])

"""
同set 但为不可变集合 不能修改 set能修改
a = set('luxury')
>>> a
set(['y', 'x', 'r', 'u', 'l'])
>>> a.add('lx')
>>> a
set(['l', 'r', 'u', 'y', 'x', 'lx'])
a = frozenset ('luxrury')
>>> a
frozenset(['y', 'x', 'r', 'u', 'l'])
>>> a.add('z')
Traceback (most recent call last):
"""

def _gen_sql(table_name, mappings):
    """
    类 ==> 表时 生成创建表的sql
    :param table_name:
    :param mappings: 映射
    :return:
    """
    pk = None
    sql = ['-- generation SQL for %s:' % table_name, 'create table `%s` (' % table_name]
    for f in sorted(mappings.values(), lambda x, y: cmp(x._order, y._order)):
        # sorted 排序 cmp(x, y) 如果x < y 返回 -1
        if not hasattr(f, 'ddl'):       # hasattr 判断f 对象是否有 'ddl' 属性 有 返回True
            raise StandardError('no ddi in field "%s".' % f)
        ddl = f.ddl
        nullable = f.nullable
        if f.primary_key:
            pk = f.name
        #sql.append(nullable and ' `%s` %s,' % (f.name, ddl) or ' `%s` %s not null, ' % (f.name, ddl))
        sql.append('  `%s` %s,' % (f.name, ddl) if nullable else '  `%s` %s not null,' % (f.name, ddl))
    sql.append(' primary key (`%s`)' % pk)
    sql.append(');')
    return '\n'.join(sql)           # .join 联合函数 将sql 指定字符连接

class Field(object):
    """
    保存数据库中的表的  字段属性
    _count: 类属性，每实例化一次，该值就+1
    self._order: 实例属性， 实例化时从类属性处得到，用于记录 该实例是 该类的第多少个实例
        例如最后的doctest：
            定义user时该类进行了5次实例化，来保存字段属性
                id = IntegerField(primary_key=True)
                name = StringField()
                email = StringField(updatable=False)
                passwd = StringField(default=lambda: '******')
                last_modified = FloatField()
            最后各实例的_order 属性就是这样的
                INFO:root:[TEST _COUNT] name => 1
                INFO:root:[TEST _COUNT] passwd => 3
                INFO:root:[TEST _COUNT] id => 0
                INFO:root:[TEST _COUNT] last_modified => 4
                INFO:root:[TEST _COUNT] email => 2
            最后生成__sql时（见_gen_sql 函数），这些字段就是按序排列
                create table `user` (
                `id` bigint not null,
                `name` varchar(255) not null,
                `email` varchar(255) not null,
                `passwd` varchar(255) not null,
                `last_modified` real not null,
                primary key(`id`)
                );
    self._default: 用于让orm自己填入缺省值，缺省值可以是 可调用对象，比如函数
                比如：passwd 字段 <StringField:passwd,varchar(255),default(<function <lambda> at 0x0000000002A13898>),UI>
                     这里passwd的默认值 就可以通过 返回的函数 调用取得
    其他的实例属性都是用来描述字段属性的

    """
    _count = 0

    def __init__(self, **kw):
        # get('a', default = None) 'a'不在字典返回空 default = True 'a' 不在字典返回True 在字典返回其key
        self.name = kw.get('name', None)
        self._default = kw.get('default', None)
        self.primary_key = kw.get('primary_key', False)
        self.nullable = kw.get('nullable', False)
        self.updatable = kw.get('updatabla', True)
        self.insertable = kw.get('insertable', True)
        self.ddl = kw.get('ddl', '')
        self._order = Field._count
        Field._count += 1

    @property                   #  使用property 将方法变成属性调用
    def default(self):
        """
        利用getter实现的一个写保护的 实例属性 为只读属性
        :return:
        """
        d = self._default
        return d() if callable(d) else d    # callable 查看能否被调用

    def __str__(self):
        """
        返回实例对象的描述信息，比如：
            <IntegerField:name,bigint,default(0),UI>
            类：实例：实例ddl属性：实例default信息，3中标志位：N U I

        :return:
        """
        s = ['< %s: %s, %s, default (%s), ' % (self.__class__.__name__, self.name, self.ddl, self._default)]
        self.nullable and s.append('N')
        self.updatable and s.append('U')
        self.insertable and s.append('I')
        s.append('>')
        return ''.join(s)

class StringField(Field):
    """
    保存String类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'varchar(255)'
        super(StringField, self).__init__(**kw)

class IntegerField(Field):
    """
    保存Integer类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = 0
        if 'ddl' not in kw:
            kw['ddl'] = 'bigint'
        super(IntegerField, self).__init__(**kw)


class FloatField(Field):
    """
    保存Float类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = 0.0
        if 'ddl' not in kw:
            kw['ddl'] = 'real'
        super(FloatField, self).__init__(**kw)


class BooleanField(Field):
    """
    保存BooleanField类型字段的属性
    """
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = False
        if not 'ddl' in kw:
            kw['ddl'] = 'bool'
        super(BooleanField, self).__init__(**kw)

class TextField(Field):
    """
    保存Text类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'text'
        super(TextField, self).__init__(**kw)


class BlobField(Field):
    """
    保存Blob类型字段的属性
    """
    def __init__(self, **kw):
        if 'default' not in kw:
            kw['default'] = ''
        if 'ddl' not in kw:
            kw['ddl'] = 'blob'
        super(BlobField, self).__init__(**kw)


class VersionField(Field):
    """
    保存Version类型字段的属性
    """
    def __init__(self, name=None):
        super(VersionField, self).__init__(name=name, default=0, ddl='bigint')

class ModelMetaclass(type):
    """
    使用metaclass 元素控制类的创建行为
    对类对象动态完成以下操作
    避免修改Model类：
        1. 排除对Model类的修改
    属性与字段的mapping：
        1. 从类的属性字典中提取出 类属性和字段类 的mapping
        2. 提取完成后移除这些类属性，避免和实例属性冲突
        3. 新增"__mappings__" 属性，保存提取出来的mapping数据
    类和表的mapping：
        1. 提取类名，保存为表名，完成简单的类和表的映射
        2. 新增"__table__"属性，保存提取出来的表名

    """
    def __new__(cls, name, bases, attrs):
        """

        :param name: 名字
        :param bases: 基本信息
        :param attrs: 属性
        :return:
        """
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        if not hasattr(cls, 'subclasses'):
            cls.subclasses = {}
        # 添加子类信息
        if not name in cls.subclasses:
            cls.subclasses[name] = name
        else:
            logging.warning('Redefine class: %s' % name)

        logging.info('Scan ORMapping %s...' % name)
        mappings = dict()
        primary_key = None
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                v.name = k
            logging.info('[MAPPING] Found mapping: %s => %s' % (k, v))
            # 检查重复主键
            if v.primary_key:
                if primary_key:                                 #不含primary_key 返回 False
                    raise TypeError('Cannot define more than 1 primary key in class: %s' % name)
                if v.updatable:                                 #不含updatable 返回 True
                    logging.warning('NOTE: change primary key to non-updatable.')
                    v.updatable = False
                if v.nullable:                                  # 不含 nullable 返回False
                    logging.warning('NOTE: change primary key to non-nullable.')
                    v.nullable = False
                primary_key = v
            mappings[k] = v
        # 检查主键是否存在
        if not primary_key:
            raise TypeError('Primary key not defined in class: %s' % name)
        for k in mappings.iterkeys():
            attrs.pop(k)
        if not '__table__' in attrs:
            attrs['__table__'] = name.lower()       # 假设表名和类名一致
        attrs['__mappings__'] = mappings            # 保存属性和列的映射关系
        attrs['__sql__'] = lambda self: _gen_sql(attrs['__table__'], mappings)
        for trigger in _triggers:
            if not trigger in attrs:
                attrs[trigger] =None
        return type.__new__(cls, name, bases, attrs)





















































