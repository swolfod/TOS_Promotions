import pickle


class RQueue(object):

    def __init__(self, redisConn, key):
        self._redis = redisConn
        self._key = key

    def get(self, timeout=5):
        value = self._redis.blpop(self._key, timeout=timeout)
        return value and pickle.loads(value[1]) or None

    def put(self, value):
        self._redis.rpush(self._key, pickle.dumps(value))

    def empty(self):
        return False if self._redis.llen(self._key) else True

    def count(self):
        return self._redis.llen(self._key)

    def clear(self):
        return self._redis.delete(self._key)
