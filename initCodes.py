__author__ = "swolfod"

import os
from django.db import transaction

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TOS_Pyramid.settings")

    import django
    django.setup()

    from TOS_Pyramid.models import *

    allCodes = [
        'BJNN12802',
        'AYDS12803',
        'AMST12804',
        'ZBJX12805',
        'WNXX12806',
        'JGXZ12807',
        'NSLX12808',
        'JNCW12809',
        'JSXX12810',
        'HYGL12811',
        'BTYX12812',
        'NDLX12813',
        'GSTX12814',
        'WKLX12815',
        'ZXJX12816',
        'JZFX12817',
        'WDZX12818',
        'AWTX12819',
        'YZSW12820',
        'PXZL12821',
        'LHXX12822',
        'TOUC12823',
        'GZGJ12824',
        'COMPJ12825',
        'YJXX12826',
        'HMLY12827',
        'SQAL12828',
        'MXLX12830',
        'MGLX12831',
        'LXGX12832',
        'ZYGL12833',
        'YXLV12834',
        'MTMT12835',
        'QTQT12836',
    ]

    promotionCodes = [PromotionCode(code=code, featured=True) for code in allCodes]
    PromotionCode.objects.bulk_create(promotionCodes)