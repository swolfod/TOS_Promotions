__author__ = 'swolfod'

import math
import re
import requests
import sys
import os
from lxml import html
from difflib import SequenceMatcher
import gzip
import string
import random
import datetime
from urllib import request, parse
import io
import collections
import copy


def str2bool(v):
    if isinstance(v, bool):
        return v

    return str(v).lower() in ("yes", "true", "t", "1")

def getBoolValue(v):
    if isinstance(v, str):
        return str2bool(v)

    return v


def calcDist(lat1, lng1, lat2, lng2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lng1, lat1, lng2, lat2 = map(math.radians, [lng1, lat1, lng2, lat2])
    # haversine formula
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km


def listAllFiles(directory):
    # returns a list of names (with extension, without full path) of all files
    # in folder path
    files = []
    for name in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, name)):
            files.append(name)
    return files

def LoadHttpString(link, postData={}, encoding=None, session=None, headers=None, timeout=30):
    for i in range(3):
        try:
            if link.find("#") >= 0:
                link = link[:link.find("#")]

            if not link.lower().startswith("http"):
                link = 'https://' + link

            requestHeaders = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
            if headers:
                requestHeaders.update(headers)

            if not session:
                session = requests.Session()

            if postData:
                res = session.post(link, data=postData, headers=requestHeaders, timeout=timeout)
            else:
                res = session.get(link, headers=requestHeaders, timeout=timeout)

            if encoding:
                res.encoding = encoding
            docContent = res.text

            """if not encoding:
                contentType = res.headers['content-type'] if 'content-type' in res.headers else None

                if not (contentType and contentType.find('charset=') >= 0):
                    contentTypeMatch = re.search(r"<meta\s+[^>]*http-equiv=['\"]Content-Type['\"]\s+[^>]*content=['\"]([^'\"]+)['\"] />",
                                                 docContent, re.IGNORECASE)
                    if contentTypeMatch:
                        contentType = contentTypeMatch.group(1)

                if contentType and contentType.find('charset=') >= 0:
                    encoding=contentType.split('charset=')[-1]
                    if encoding.lower() == 'gb2312':
                        encoding = 'gb18030'
            if encoding:
                try:
                    docContent = docContent.decode(encoding)
                except:
                    pass"""

            return res.url, docContent, session
        except Exception as e:
            if i == 2:
                raise


def ConstructHtmlDoc(htmlStr):
    stderr = sys.stderr
    try:
        sys.stderr = os.devnull
        return html.fromstring(htmlStr)
    finally:
        sys.stderr = stderr


def HtmlEncode(strToEncode):
    return html.escape(strToEncode)


def HtmlDecode(htmlStr):
    return htmlStr.replace('&#39;', "'").replace('&quot;', '"').replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')


def GetUnicode(unicodeStr):
    result = ""

    while "\\u" in unicodeStr:
        markIndex = unicodeStr.index("\\u")
        prefix = unicodeStr[:markIndex]

        hexChar = unicodeStr[markIndex + 2:markIndex+6]
        charCode = int(hexChar, 16)
        result += prefix + chr(charCode)

        unicodeStr = unicodeStr[markIndex+6:]

    result += unicodeStr
    return result


def FixLink(linkUrl, srcPageUrl):
    linkUrl = HtmlDecode(linkUrl.strip())

    if linkUrl.lower().startswith("http") or not srcPageUrl.lower().startswith("http"):
        return linkUrl

    if linkUrl.startswith("/"):
        end = srcPageUrl.find("/", srcPageUrl.index("://") + 3)
    elif linkUrl.startswith("?"):
        end = srcPageUrl.find("?")
    else:
        end = srcPageUrl.rfind("/") + 1

    if end < 0:
        end = len(srcPageUrl)
    return srcPageUrl[0:end] + linkUrl


def GetLxmlNodeText(lxmlNode):
    nodeText = ""
    for text in lxmlNode.itertext():
        nodeText += " " + text.strip()

    return nodeText.lstrip()


def LoadXmlNodesText(parentNode, selectPath):
    return [selectedNode.strip() if isinstance(selectedNode, str) else GetLxmlNodeText(selectedNode) for selectedNode in parentNode.xpath(selectPath)]


def LoadCombinedXmlNodesText(parentNode, selectPath):
    return " ".join(LoadXmlNodesText(parentNode, selectPath))


def LoadSingleXmlNodeText(parentNode, selectPath):
    selectedNode = parentNode.xpath(selectPath)
    if selectedNode:
        node = selectedNode[0]
        return node.strip() if isinstance(node, str) else GetLxmlNodeText(node)
    else:
        return None


def ClearComments(doc):
    comments = doc.xpath("//comment()")
    for comment in comments:
        comment.getparent().remove(comment)

def GetInnerText(lxmlNode):
    if lxmlNode is None:
        return ""

    childText = [html.tostring(child, encoding="unicode") for child in lxmlNode.iterchildren()]
    return (lxmlNode.text or '') + ''.join(childText)


def GetSubdirectories(directory):
    return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]


def GetFiles(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]


def decimalizeLatLng(lat_lon_str):
    parts = lat_lon_str.split()
    latStr = parts[0].strip()
    lngStr = parts[1].strip()

    return decimalizeGeoCoord(latStr, True), decimalizeGeoCoord(lngStr, False)


def decimalize(degrees, minutes, seconds, direction):
    decimal = int(degrees) + int(minutes if minutes else 0) / 60 + float(seconds if seconds else 0) / 3600
    if direction in 'SW':
        decimal = -decimal
    return decimal


def decimalizeGeoCoord(coordStr, isLat=True):
    regex = r"""(\d+)°(?:-?(\d+)′(?:-?([\d+.]+)″)?)?([NS])""" if isLat else r"""(\d+)°(?:-?(\d+)′(?:-?([\d+.]+)″)?)?([EW])"""
    match = re.match(regex, coordStr.strip())
    if not match:
        raise ValueError("Invalid input string: {0:r}".format(coordStr))

    return decimalize(*match.groups())


def similarity(a, b, caseSensitive=True):
    if not caseSensitive:
        a = a.lower()
        b = b.lower()

    return SequenceMatcher(None, a, b).ratio()


def toEast(lngSrc, lngDst):
    distance = lngDst - lngSrc
    if distance < 0:
        distance += 360

    return distance < 180


def fetch(url, data=None, proxies=None, user_agent='Mozilla/5.0', timeout=30, printError=True, retries=3):
    """Download the content at this url and return the content
"""
    tried = 0
    content = None

    while tried < retries:
        try:
            opener = request.build_opener()
            proxy = None
            if proxies:
                # download through a random proxy from the list
                proxy = random.choice(proxies)
                if url.lower().startswith('https://'):
                    opener.add_handler(request.ProxyHandler({'https' : proxy}))
                else:
                    opener.add_handler(request.ProxyHandler({'http' : proxy}))

            # submit these headers with the request
            headers =  {'User-agent': user_agent, 'Accept-encoding': 'gzip', 'Referer': url}

            #print(url, proxy)

            if isinstance(data, dict):
                # need to post this data
                data = parse.urlencode(data)
            response = opener.open(request.Request(url, data, headers), timeout=timeout)
            content = response.read()
            if response.headers.get('content-encoding') == 'gzip':
                # data came back gzip-compressed so decompress it
                content = gzip.GzipFile(fileobj=io.BytesIO(content)).read()

            encoding = 'UTF-8'
            content = content.decode(encoding=encoding)
        except Exception as e:
            # so many kinds of errors are possible here so just catch them all
            if printError:
                print('Error: %s %s' % (url if not proxy else proxy, e))
            content = None
        finally:
            tried += 1
            if content:
                break

    if proxies:
        return content, proxy
    else:
        return content

def filePathFromUrl(url, root):
    url = url.strip()

    if "://" in url:
        url = url[url.index("://") + 3:]

    if "/" in url:
        url = url[url.index("/") + 1:]

    if "." in url and ("/" not in url or url.rindex(".") > url.rindex("/")):
        url = url[:url.rindex(".")]

    filePath = url + ".txt"

    if root:
        filePath = root + "/" + filePath

    basedir = os.path.dirname(filePath)
    if not os.path.isdir(basedir):
        os.makedirs(basedir)

    return filePath


def deepUpdate(oriDict, newDict):
    for key, val in newDict.items():
        if isinstance(val, collections.Mapping):
            deepUpdate(oriDict.setdefault(key, {}), val)
        elif isinstance(val, list):
            oriDict[key] = oriDict.get(key, []) + val
        else:
            oriDict[key] = newDict[key]

    return oriDict


def extractData(oriData, fields=None):
    if fields == None:
        return copy.deepcopy(oriData)

    if oriData == None:
        return None

    result = {}

    for k, v in fields.items():
        if k not in oriData:
            continue

        oriValue = oriData[k]
        if isinstance(v, collections.Mapping) and oriValue != None:
            if isinstance(oriValue, list):
                result[k] = [extractData(oriItem, v) for oriItem in oriValue]
            else:
                result[k] = extractData(oriValue, v)
        elif v:
            result[k] = copy.deepcopy(oriValue)

    return result


def deepFlatten(objList):
    result = []
    for obj in objList:
        if isinstance(obj, list):
            result += deepFlatten(obj)
        else:
            result.append(obj)

    return result


def imageSize(imgSrc):
    try:
        match = re.search('[a-zA-Z0-9]{32}_([0-9]{0,5})x([0-9]{0,5})', imgSrc, re.IGNORECASE)
        return int(match.group(1)), int(match.group(2))
    except:
        return 0, 0


def extractDomain(netloc):
    if ":" in netloc:
        netloc = netloc[:netloc.index(":")]

    return netloc[netloc.index(".") + 1:]

    lastDotIdx = netloc.rindex(".")
    dotIdx = netloc.index(".")
    while dotIdx != lastDotIdx:
        netloc = netloc[dotIdx + 1:]
        dotIdx = netloc.index(".")
        lastDotIdx = netloc.rindex(".")

    return netloc


def calculateBounds(locations):
    latitudes = sorted([location["lat"] for location in locations])
    longitudes = sorted([location["lng"] for location in locations])

    latS = latitudes[0]
    latN = latitudes[-1]
    latDist = latN - latS
    latN += latDist / 20
    if latN > 85:
        latN = 85

    latS -= latDist / 20
    if latS < -85:
        latS = -85


    lngW = longitudes[0]
    lngE = longitudes[-1]
    minLngDis = lngE - lngW

    for i in range(0, len(longitudes) - 1):
        lngDis = longitudes[i] - longitudes[i + 1] + 360
        if lngDis < minLngDis:
            minLngDis = lngDis
            lngE = longitudes[i]
            lngW = longitudes[i + 1]

    lngE += minLngDis / 20
    if lngE > 180:
        lngE -= 360

    lngW -= minLngDis / 20
    if lngW < -180:
        lngW += 360

    return {
        "latN": latN,
        "latS": latS,
        "lngE": lngE,
        "lngW": lngW
    }


def latRad(lat):
    sin = math.sin(lat * math.pi / 180)
    radX2 = math.log((1 + sin) / (1 - sin)) / 2
    return max(min(radX2, math.pi), -math.pi) / 2


def radLat(rad):
    radX2 = max(min(rad * 2, math.pi), -math.pi)
    tSin= math.e ** (radX2 * 2)
    sin = (tSin - 1) / (tSin + 1)
    return math.asin(sin) / math.pi * 180


def getGoogleMapZoom(latN, lngE, latS, lngW, mapWidth=300, mapHeight=300):
    worldDimH = 256
    worldDimW = 256
    zoomMax = 21

    if latN == latS or lngE == lngW:
        return zoomMax

    def zoom(mapPx, worldPx, fraction):
        return math.floor(math.log(mapPx / worldPx / fraction) / math.log(2))

    latFraction = (latRad(latN) - latRad(latS)) / math.pi

    lngDiff = lngE - lngW
    lngFraction = ((lngDiff + 360) if lngDiff < 0 else lngDiff) / 360

    latZoom = zoom(mapHeight, worldDimH, latFraction)
    lngZoom = zoom(mapWidth, worldDimW, lngFraction)

    return min(latZoom, lngZoom, zoomMax)


def getGoogleMapPosByPixelOffset(oriLat, oriLng, zoom, latPixel, lngPixel):
    worldDimH = 256 * 2 ** zoom
    worldDimW = 256 * 2 ** zoom

    latFraction = latPixel / worldDimH
    targetRad = latFraction * math.pi + latRad(oriLat)
    targetLat = radLat(targetRad)

    lngFraction = lngPixel / worldDimW
    targetLng = lngFraction * 360 + oriLng
    while targetLng > 180:
        targetLng -= 360
    while targetLng < -180:
        targetLng += 360

    return targetLat, targetLng


def getGoogleStaticMapUrl(lat, lng, zoom, width, height, scale=1, language="en", format="jpg", markers=None, path=None):
    markerParam = ""
    if scale != 2:
        scale = 1

    if markers:
        markerArr = []
        for marker in markers:
            parts = ["scale:{0}".format(scale)]

            if marker["icon"]:
                parts.append("icon:{0}".format(marker["icon"]))

            for location in marker["locations"]:
                parts.append("{0},{1}".format(location["lat"], location["lng"]))

            markerArr.append("&markers=" + parse.quote("|".join(parts)))

        markerParam = "".join(markerArr)

    pathParam = ""
    if path:
        parts = []

        if path["color"]:
            parts.append("color:{0}".format(path["color"]))

        if path["weight"]:
            parts.append("weight:{0}".format(path["weight"]))

        for point in path["points"]:
            parts.append("{0},{1}".format(point["lat"], point["lng"]))

        pathParam = "&path=" + parse.quote("|".join(parts))

    return "https://ditu.google.cn/maps/api/staticmap?center={0},{1}&zoom={2}&size={3}x{4}{5}{6}&scale={7}&language={8}&format={9}&key=AIzaSyAVzkS9fJtCinveTrOC1YM7_4BJ4f86R1o"\
        .format(lat, lng, zoom, width, height, markerParam, pathParam, scale, language, format)


def is_ascii(s):
    return all(ord(c) < 128 for c in s)

from xml.dom import minidom
from collections import Mapping


def dict2element(root, structure, doc):
    """
    Gets a dictionary like structure and converts its
    content into xml elements. After that appends
    resulted elements to root element. If root element
    is a string object creates a new elements with the
    given string and use that element as root.
    This function returns a xml element object.
    """
    assert isinstance(structure, Mapping), \
        'Structure must be a mapping object such as dict'

    # if root is a string make it a element
    if isinstance(root, str):
        root = doc.createElement(root)

    for key, value in structure.items():
        el = doc.createElement("" if key is None else key)
        if isinstance(value, Mapping):
            dict2element(el, value, doc)
        else:
            el.appendChild(doc.createTextNode("" if value is None
                                              else value))
        root.appendChild(el)

    return root


def dict2xml(structure, tostring=False):
    """
    Gets a dict like object as a structure and returns a corresponding minidom
    document object.
    If str is needed instead of minidom, tostring parameter can be used
    Restrictions:
    Structure must only have one root.
    Structure must consist of str or dict objects (other types will
    converted into string)
    Sample structure object would be
    {'root':{'elementwithtextnode':'text content',
             'innerelements':{'innerinnerelements':'inner element content'}}}
    result for this structure would be
    '<?xml version="1.0" ?>
    <root>
      <innerelements>
      <innerinnerelements>inner element content</innerinnerelements>
      </innerelements>
      <elementwithtextnode>text content</elementwithtextnode>
    </root>'
    """
    # This is main function call. which will return a document
    assert len(structure) == 1, 'Structure must have only one root element'
    assert isinstance(structure, Mapping), \
        'Structure must be a mapping object such as dict'

    root_element_name, value = next(iter(structure.items()))
    impl = minidom.getDOMImplementation()
    doc = impl.createDocument(None, root_element_name, None)
    dict2element(doc.documentElement, value, doc)
    return doc.toxml() if tostring else doc


def randomString(length=16):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def dateRange(start_date, end_date):
    if start_date <= end_date:
        for n in range(( end_date - start_date ).days + 1):
            yield start_date + datetime.timedelta( n )
    else:
        for n in range( ( start_date - end_date ).days + 1 ):
            yield start_date - datetime.timedelta( n )