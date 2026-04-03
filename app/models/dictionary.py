# -*- coding: utf-8 -*-
"""
数据字典模型
"""

from datetime import datetime
from app.extensions import db


class DictType(db.Model):
    """字典类型表"""
    
    __tablename__ = 'dict_type'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='字典类型ID')
    dict_name = db.Column(db.String(100), nullable=False, comment='字典名称')
    dict_code = db.Column(db.String(100), unique=True, nullable=False, index=True, comment='字典编码')
    description = db.Column(db.String(500), nullable=True, comment='描述')
    status = db.Column(db.Boolean, nullable=False, default=True, comment='状态：0-禁用，1-启用')
    is_system = db.Column(db.Boolean, nullable=False, default=False, comment='是否系统内置')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    items = db.relationship('DictItem', foreign_keys='DictItem.dict_type_id', backref='dict_type', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DictType {self.dict_code}>'


class DictItem(db.Model):
    """字典项目表"""
    
    __tablename__ = 'dict_item'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='字典项ID')
    dict_type_id = db.Column(db.Integer, db.ForeignKey('dict_type.id'), nullable=False, index=True, comment='字典类型ID')
    item_label = db.Column(db.String(200), nullable=False, comment='字典标签')
    item_value = db.Column(db.String(200), nullable=False, comment='字典键值')
    description = db.Column(db.String(500), nullable=True, comment='描述')
    status = db.Column(db.Boolean, nullable=False, default=True, comment='状态：0-禁用，1-启用')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序')
    css_class = db.Column(db.String(100), nullable=True, comment='样式属性')
    is_default = db.Column(db.Boolean, nullable=False, default=False, comment='是否默认')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<DictItem {self.item_label}>'


def init_system_dicts():
    """初始化系统内置字典数据"""
    # 检查是否已初始化
    if DictType.query.filter_by(is_system=True).count() > 0:
        return
    
    # 系统状态字典
    status_type = DictType(
        dict_name='系统状态',
        dict_code='system_status',
        description='通用系统状态字典',
        is_system=True,
        sort_order=1
    )
    status_items = [
        DictItem(item_label='启用', item_value='1', is_default=True, sort_order=1, css_class='success'),
        DictItem(item_label='禁用', item_value='0', sort_order=2, css_class='danger')
    ]
    status_type.items.extend(status_items)
    
    # 性别字典
    gender_type = DictType(
        dict_name='性别',
        dict_code='gender',
        description='用户性别字典',
        is_system=True,
        sort_order=2
    )
    gender_items = [
        DictItem(item_label='男', item_value='male', is_default=True, sort_order=1),
        DictItem(item_label='女', item_value='female', sort_order=2),
        DictItem(item_label='未知', item_value='unknown', sort_order=3)
    ]
    gender_type.items.extend(gender_items)
    
    # 备件状态字典
    spare_status_type = DictType(
        dict_name='备件状态',
        dict_code='spare_status',
        description='备件库存状态字典',
        is_system=True,
        sort_order=3
    )
    spare_status_items = [
        DictItem(item_label='正常', item_value='normal', is_default=True, sort_order=1, css_class='success'),
        DictItem(item_label='库存不足', item_value='low_stock', sort_order=2, css_class='warning'),
        DictItem(item_label='缺货', item_value='out_of_stock', sort_order=3, css_class='danger'),
        DictItem(item_label='待采购', item_value='pending_purchase', sort_order=4, css_class='info')
    ]
    spare_status_type.items.extend(spare_status_items)
    
    # 交易类型字典
    transaction_type = DictType(
        dict_name='交易类型',
        dict_code='transaction_type',
        description='出入库交易类型字典',
        is_system=True,
        sort_order=4
    )
    transaction_items = [
        DictItem(item_label='入库', item_value='inbound', sort_order=1, css_class='success'),
        DictItem(item_label='出库', item_value='outbound', sort_order=2, css_class='danger'),
        DictItem(item_label='调拨', item_value='transfer', sort_order=3, css_class='info'),
        DictItem(item_label='盘点', item_value='stocktake', sort_order=4, css_class='warning')
    ]
    transaction_type.items.extend(transaction_items)
    
    # 维修状态字典
    maintenance_type = DictType(
        dict_name='维修状态',
        dict_code='maintenance_status',
        description='设备维修状态字典',
        is_system=True,
        sort_order=5
    )
    maintenance_items = [
        DictItem(item_label='待维修', item_value='pending', is_default=True, sort_order=1, css_class='warning'),
        DictItem(item_label='维修中', item_value='in_progress', sort_order=2, css_class='info'),
        DictItem(item_label='已完成', item_value='completed', sort_order=3, css_class='success'),
        DictItem(item_label='已取消', item_value='cancelled', sort_order=4, css_class='secondary')
    ]
    maintenance_type.items.extend(maintenance_items)
    
    # 优先级字典
    priority_type = DictType(
        dict_name='优先级',
        dict_code='priority',
        description='任务优先级字典',
        is_system=True,
        sort_order=6
    )
    priority_items = [
        DictItem(item_label='低', item_value='low', sort_order=1, css_class='secondary'),
        DictItem(item_label='中', item_value='medium', is_default=True, sort_order=2, css_class='info'),
        DictItem(item_label='高', item_value='high', sort_order=3, css_class='warning'),
        DictItem(item_label='紧急', item_value='urgent', sort_order=4, css_class='danger')
    ]
    priority_type.items.extend(priority_items)
    
    # 保存到数据库
    db.session.add_all([
        status_type, gender_type, spare_status_type,
        transaction_type, maintenance_type, priority_type
    ])
    db.session.commit()
