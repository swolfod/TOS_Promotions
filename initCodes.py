__author__ = "swolfod"

import os
from django.db import transaction

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TOS_Pyramid.settings")

    import django
    django.setup()

    from TOS_Pyramid.models import *

    codesSrc = """
贝妮吉吉	442		BJNN12802
遨游大师	*	AYDS12803
amstardmc	688		AMST12804
住百家	－	ZBJX12805
唯恩	613		WNXX12806
中青旅耀悦	663		JGXZ12807
诺思旅行	21	NSLX12808
济南传唯信息咨询有限公司	675		JNCW12809
踏沙行	606 	JSXX12810
海洋国旅	219		HYGL12811
纷途游	* 	BTYX12812
你定旅行	583		NDLX12813
卧客旅行	687		WKLX12815
知行家	145		ZXJX12816
九州风行	154		JZFX12817
五大洲商旅	173		WDZX12818
爱玩兔	49	AWTX12819
亚洲商务航空俱乐部	649		YZSW12820
品行之旅	152		PXZL12821
领航	539		LHXX12822
Touchtrips	83	TOUC12823
贵州国际旅行社	236		GZGJ12824
compass	51	COMPJ12825
译见	－	YJXX12826
赫美旅业	653		HMLY12827
上汽阿里	*	SQAL12828
梦想旅行	－		MXLX12830
蘑菇旅行	－	MGLX12831
理想国	421		LXGX12832
竹园国旅	431		ZYGL12833
游心	47	YXLV12834
北京环亚风景国际旅行社	706	THGC14011
媒体	*	MTMT12835
""".strip().split("\n")

    allCodes = [row.split("\t") for row in codesSrc]

    try:
        organization = Organization.objects.get(pk=706)
    except:
        Organization(id=706, name="北京环亚风景国际旅行社").save()

    for codeParts in allCodes:
        orgName = codeParts[0].strip()
        orgId = codeParts[1].strip()
        code = codeParts[2].strip()

        promotionCode = PromotionCode.objects.filter(code=code).first()
        if not promotionCode:
            promotionCode = PromotionCode(code=code)

        if orgId == "-":
            promotionCode.organization_id = None
            promotionCode.featured = False
        elif orgId == "*":
            promotionCode.organization_id = None
            promotionCode.featured = True
        else:
            promotionCode.organization_id = orgId
            promotionCode.featured = True

        promotionCode.save()