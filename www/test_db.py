# -*- coding: utf-8 -*-

from models import User, Blog, Comment
from transwarp import db

db.create_engine('root','123456', 'awesome','localhost')
u = Blog(name='Test3', summary='Luxury', content='1234567890')

u.insert()

# print 'new user id:', u.id
#
# u1 = User.find_first('where email=?', 'lxlx644966783@sina.com')
# print 'find user\'s name:', u1.name
#
# u1.delete()




