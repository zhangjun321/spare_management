"""
服务层
封装业务逻辑
"""

# 新的仓库管理模块服务
from app.services.inbound_linkage_service import InboundLinkageService
from app.services.outbound_linkage_service import OutboundLinkageService
from app.services.baidu_qianfan_service import BaiduQianfanService, get_qianfan_service

__all__ = [
    'InboundLinkageService',
    'OutboundLinkageService',
    'BaiduQianfanService',
    'get_qianfan_service'
]
