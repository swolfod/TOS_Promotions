import json
from .utils import LoadHttpString

API_KEY = "70c084fd93f6088e48cf82eedaf96e9b"
HOST = "sms.yunpian.com"
PORT = 443
VERSION = "v1"
METHOD = "/sms/send.json"
SMS_LINK = "https://{}:{}/{}{}".format(HOST, PORT, VERSION, METHOD)


def send(mobile, text):
    """
    Parameter description please refer to https://www.yunpian.com/api/sms.html
    """
    url, content, session = LoadHttpString(SMS_LINK, {"apikey": API_KEY, "mobile": mobile, "text": text})
    result = json.loads(content)
    return {
        "code": result["code"],
        "msg": result["msg"]
    }
