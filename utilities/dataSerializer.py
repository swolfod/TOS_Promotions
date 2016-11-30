__author__ = 'swolfod'

from . import djangoUtils
from datetime import datetime


class DataSerializer:
    def __init__(self, dataObj, fields, attrMap=None):
        self._dataObj = dataObj
        self._fields = fields
        self._attrMap = attrMap or {}


    def getAttribute(self, attr, fields):
        attr = self._attrMap.get(attr, attr)

        try:
            attrFunc = getattr(self, attr)
        except AttributeError:
            obj = self._dataObj

            for attr in attr.split("."):
                obj = getattr(obj, attr)
        else:
            obj = attrFunc(fields)

        return obj


    @property
    def data(self):
        if not self._dataObj:
            return None

        if self._fields is True:
            return self.id()

        return { k: self.getAttribute(k, v) for k, v in self._fields.items() if v }


    def id(self, fields=None):
        return djangoUtils.encodeId(self._dataObj.id)
