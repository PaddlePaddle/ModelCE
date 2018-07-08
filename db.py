import bson
from pymongo import MongoClient
import redis
from utils import log, dictobj
import datetime

class MongoDB(object):
    '''
    MongoDB can store data that is larger than memory, so it is more sutable for CE
    than Redis.
    '''

    def __init__(self, host='localhost', port=27017, db="0", test=False):
        if test:
            log.warn('Using MongoDB in test mode')
        db = "test" if test else db
        self.test = test
        self.client = MongoClient(host, port)
        self.db = getattr(self.client, db)

    def tables(self):
        return self.db.collection_names(include_system_collections=False)

    def table(self, table=None):
        return self.db.posts if not table else getattr(self.db, table)

    def set(self, key, value, table=None):
        if type(value) is str:
            value = {'json': value}
        cond = {'key': key} if type(key) is str else key
        value.update(cond)
        value['date'] = datetime.datetime.utcnow()
        return self.table(table).insert_one(value)

    def get(self, key, table=None):
        '''
        Get a record according to key or a dict.
        :param key: str or dict
        :return: dict or None
        '''
        search_key = {'key':key} if type(key) is str else key
        record = self.table(table).find_one(search_key)
        return dictobj(record) if record else None

    def gets(self, key, table=None):
        '''
        Search multiply record one time.
        :param key: str or dict
        :param table:
        :return: list of dict
        '''
        search_key = {'key':key} if type(key) is str else key
        record = self.table(table).find(search_key)
        return [dictobj(r) for r in record]

    def delete(self, key, table=None):
        search_key = {'key':key} if type(key) is str else key
        return self.table(table).remove(search_key)


class RedisDB(object):
    ''' An higher interface for the Redis database. '''

    def __init__(self, host='localhost', port=6379, db=0, test=False):
        db = 15 if test else db
        self.test = test
        self.rd = redis.StrictRedis(host=host, port=port, db=db, encoding="utf-8", decode_responses=True)
        log.warn('Connect DB in %s:%d, id: %d' % (host, port, db))
        if test:
            log.warn('Run DB in testing mode.')

    def set(self, key, value):
        '''
        Set a record.
        :param key(str): the id of this record.
        :param value(str): the value of this record
        :return: bool(whether succeed)
        '''
        self.rd.set(key, value)

    def get(self, key):
        '''
        Query a record.

        :param key(str): id of the record
        :return: str or None
        '''
        return self.rd.get(key)

    def delete(self, *keys):
        '''
        Delete one or more records.

        :param key(str): id of the record.
        :return: bool (succeed)
        '''
        return self.rd.delete(*keys)

    def publish_message(self, channel, message):
        '''
        Publish a message to a channel.

        :param channel(str: name of a channel.
        :param message(str): content of a message.
        :return:
          - int: number of channels it sends to.
        '''
        return self.rd.publish(channel, message)

    def new_subpub(self):
        '''
        Create a new publish subscribe pattern.
        '''
        return self.rd.pubsub()



