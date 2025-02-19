#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.com>
#         http://binux.me
# Created on 2012-08-30 17:43:49

import sqlite3
import config
from libs.log import Log

logger_DB = Log('qiandao.Database').getlogger()

def tostr(s):
    if isinstance(s, bytes):
        try:
            return s.decode()
        except :
            return s
    if isinstance(s, bytearray):
        try:
            return s.decode()
        except :
            return s
    return s
    

class BaseDB(object):
    '''
    BaseDB

    dbcur should be overwirte
    '''
    placeholder = "%s" # mysql
    # placeholder = '?' # sqlite3

    def __init__(self, host=config.mysql.host, port=config.mysql.port,
            database=config.mysql.database, user=config.mysql.user, passwd=config.mysql.passwd, auth_plugin=config.mysql.auth_plugin):
        import mysql.connector
        self.conn = mysql.connector.connect(user=user, password=passwd, host=host, port=port,
                database=database, auth_plugin=auth_plugin, autocommit=True)

    @staticmethod
    def escape(string):
        return '`%s`' % string

    @property
    def dbcur(self):
        if self.conn.unread_result:
            try:
                self.conn.get_rows()
            except:
                pass
        self.conn.ping(reconnect=True)
        return self.conn.cursor()

    def _execute(self, sql_query, values=[]):
        dbcur = self.dbcur
        dbcur.execute(sql_query, values)
        return dbcur
    
    def _select(self, tablename=None, what="*", where="", where_values=[], offset=0, limit=None):
        tablename = self.escape(tablename or self.__tablename__)
        if isinstance(what, list) or isinstance(what, tuple) or what is None:
            what = ','.join(self.escape(f) for f in what) if what else '*'

        sql_query = "SELECT %s FROM %s" % (what, tablename)
        if where: sql_query += " WHERE %s" % where
        if limit: sql_query += " LIMIT %d, %d" % (offset, limit)
        logger_DB.debug("<sql: %s>", sql_query)

        dbcur = self._execute(sql_query, where_values)
        for row in dbcur:
            yield [tostr(x) for x in row]
        dbcur.close()

    def _select2dic(self, tablename=None, what="*", where="", where_values=[], offset=0, limit=None):
        tablename = self.escape(tablename or self.__tablename__)
        if isinstance(what, list) or isinstance(what, tuple) or what is None:
            what = ','.join(self.escape(f) for f in what) if what else '*'

        sql_query = "SELECT %s FROM %s" % (what, tablename)
        if where: sql_query += " WHERE %s" % where
        if limit: sql_query += " LIMIT %d, %d" % (offset, limit)
        logger_DB.debug("<sql: %s>", sql_query)

        dbcur = self._execute(sql_query, where_values)
        fields = [f[0] for f in dbcur.description]

        rtv = []
        for row in dbcur:
            rtv.append(dict(zip(fields, [tostr(x) for x in row])))
            #yield dict(zip(fields, [tostr(x) for x in row]))

        dbcur.close()
        return rtv
 
    def _replace(self, tablename=None, **values):
        tablename = self.escape(tablename or self.__tablename__)
        if values:
            _keys = ", ".join(self.escape(k) for k in values.keys())
            _values = ", ".join([self.placeholder, ] * len(values))
            sql_query = "REPLACE INTO %s (%s) VALUES (%s)" % (tablename, _keys, _values)
        else:
            sql_query = "REPLACE INTO %s DEFAULT VALUES" % tablename
        logger_DB.debug("<sql: %s>", sql_query)
        
        if values:
            dbcur = self._execute(sql_query, list(values.values()))
        else:
            dbcur = self._execute(sql_query)
        lastrowid = dbcur.lastrowid
        dbcur.close()
        return lastrowid
 
    def _insert(self, tablename=None, **values):
        tablename = self.escape(tablename or self.__tablename__)
        if values:
            _keys = ", ".join((self.escape(k) for k in values.keys()))
            _values = ", ".join([self.placeholder, ] * len(values))
            sql_query = "INSERT INTO %s (%s) VALUES (%s)" % (tablename, _keys, _values)
        else:
            sql_query = "INSERT INTO %s DEFAULT VALUES" % tablename
        logger_DB.debug("<sql: %s>", sql_query)
        
        if values:
            dbcur = self._execute(sql_query, list(values.values()))
        else:
            dbcur = self._execute(sql_query)
        lastrowid = dbcur.lastrowid
        dbcur.close()
        return lastrowid

    def _update(self, tablename=None, where="1=0", where_values=[], **values):
        tablename = self.escape(tablename or self.__tablename__)
        _key_values = ", ".join(["%s = %s" % (self.escape(k), self.placeholder) for k in values.keys()]) 
        sql_query = "UPDATE %s SET %s WHERE %s" % (tablename, _key_values, where)
        logger_DB.debug("<sql: %s>", sql_query)
        
        dbcur = self._execute(sql_query, list(values.values())+list(where_values))
        dbcur.close()
        return 
    
    def _delete(self, tablename=None, where="1=0", where_values=[]):
        tablename = self.escape(tablename or self.__tablename__)
        sql_query = "DELETE FROM %s" % tablename
        if where: sql_query += " WHERE %s" % where
        logger_DB.debug("<sql: %s>", sql_query)

        dbcur = self._execute(sql_query, where_values)
        dbcur.close()
        return 
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    class DB(BaseDB):
        __tablename__ = "test"
        def __init__(self):
            self.placeholder='?'
            self.conn = sqlite3.connect(":memory:")
            cursor = self.conn.cursor()
            cursor.execute('''CREATE TABLE `%s` (id INTEGER PRIMARY KEY AUTOINCREMENT, name, age)'''
                    % self.__tablename__)
              
        @property
        def dbcur(self):
            return self.conn.cursor()

    db = DB()
    assert db._insert(db.__tablename__, name="binux", age=23) == 1
    assert next(db._select(db.__tablename__, "name, age")) == ["binux", 23]
    assert db._select2dic(db.__tablename__, "name, age")[0]["name"] == "binux"
    assert db._select2dic(db.__tablename__, "name, age")[0]["age"] == 23
    db._replace(db.__tablename__, id=1, age=24)
    assert next(db._select(db.__tablename__, "name, age")) == [None, 24]
    db._update(db.__tablename__, "id = 1", age=16)
    assert next(db._select(db.__tablename__, "name, age")) == [None, 16]
    db._delete(db.__tablename__, "id = 1")
    assert list(db._select(db.__tablename__)) == []
