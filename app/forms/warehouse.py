"""
仓库管理表单
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class WarehouseForm(FlaskForm):
    """仓库表单"""
    
    name = StringField('仓库名称', validators=[
        DataRequired(message='请输入仓库名称'),
        Length(max=100)
    ], description='仓库的名称')
    
    code = StringField('仓库编码', validators=[
        DataRequired(message='请输入仓库编码'),
        Length(max=50)
    ], description='仓库的唯一编码')
    
    type = SelectField('仓库类型', validators=[
        DataRequired(message='请选择仓库类型')
    ], choices=[
        ('general', '普通仓库'),
        ('cold', '冷库'),
        (' hazardous', '危险品仓库'),
        ('valuable', '贵重物品仓库')
    ], description='仓库的类型')
    
    manager_id = SelectField('仓库管理员', validators=[
        Optional()
    ], coerce=int, description='负责管理仓库的用户')
    
    address = StringField('仓库地址', validators=[
        Optional(),
        Length(max=500)
    ], description='仓库的详细地址')
    
    area = IntegerField('仓库面积', validators=[
        Optional(),
        NumberRange(min=1, message='面积必须大于0')
    ], description='仓库的面积（平方米）')
    
    capacity = IntegerField('仓库容量', validators=[
        Optional(),
        NumberRange(min=1, message='容量必须大于0')
    ], description='仓库的容量（件）')
    
    phone = StringField('联系电话', validators=[
        Optional(),
        Length(max=20)
    ], description='仓库的联系电话')
    
    description = TextAreaField('仓库描述', validators=[
        Optional(),
        Length(max=500)
    ], description='仓库的详细描述')
    
    is_active = BooleanField('是否启用', default=True, description='是否启用该仓库')
    
    submit = SubmitField('保存')


class WarehouseLocationForm(FlaskForm):
    """库位表单"""
    
    warehouse_id = SelectField('所属仓库', validators=[
        DataRequired(message='请选择所属仓库')
    ], coerce=int, description='库位所属的仓库')
    
    location_code = StringField('库位编码', validators=[
        DataRequired(message='请输入库位编码'),
        Length(max=50)
    ], description='库位的唯一编码')
    
    location_name = StringField('库位名称', validators=[
        Optional(),
        Length(max=100)
    ], description='库位的名称')
    
    location_type = SelectField('库位类型', validators=[
        Optional()
    ], choices=[
        ('shelf', '货架'),
        ('bin', '料箱'),
        ('pallet', '托盘'),
        ('area', '区域')
    ], description='库位的类型')
    
    max_capacity = IntegerField('最大容量', validators=[
        Optional(),
        NumberRange(min=1, message='容量必须大于0')
    ], description='库位的最大容量（件）')
    
    status = SelectField('状态', validators=[
        DataRequired(message='请选择状态')
    ], choices=[
        ('available', '可用'),
        ('occupied', '已占用'),
        ('maintenance', '维护中'),
        ('disabled', '禁用')
    ], description='库位的状态')
    
    remark = TextAreaField('备注', validators=[
        Optional(),
        Length(max=500)
    ], description='库位的备注信息')
    
    submit = SubmitField('保存')


class InventoryAdjustForm(FlaskForm):
    """库存调整表单"""
    
    warehouse_id = SelectField('仓库', validators=[
        DataRequired(message='请选择仓库')
    ], coerce=int, description='调整库存的仓库')
    
    location_id = SelectField('库位', validators=[
        DataRequired(message='请选择库位')
    ], coerce=int, description='调整库存的库位')
    
    spare_part_id = SelectField('备件', validators=[
        DataRequired(message='请选择备件')
    ], coerce=int, description='调整库存的备件')
    
    quantity = IntegerField('调整数量', validators=[
        DataRequired(message='请输入调整数量'),
        NumberRange(min=-999999, max=999999, message='数量范围无效')
    ], description='调整的数量，正数为增加，负数为减少')
    
    remark = TextAreaField('备注', validators=[
        Optional(),
        Length(max=500)
    ], description='调整的备注信息')
    
    submit = SubmitField('调整')


class InventoryTransferForm(FlaskForm):
    """库存调拨表单"""
    
    from_warehouse_id = SelectField('源仓库', validators=[
        DataRequired(message='请选择源仓库')
    ], coerce=int, description='调拨的源仓库')
    
    from_location_id = SelectField('源库位', validators=[
        DataRequired(message='请选择源库位')
    ], coerce=int, description='调拨的源库位')
    
    to_warehouse_id = SelectField('目标仓库', validators=[
        DataRequired(message='请选择目标仓库')
    ], coerce=int, description='调拨的目标仓库')
    
    to_location_id = SelectField('目标库位', validators=[
        DataRequired(message='请选择目标库位')
    ], coerce=int, description='调拨的目标库位')
    
    spare_part_id = SelectField('备件', validators=[
        DataRequired(message='请选择备件')
    ], coerce=int, description='调拨的备件')
    
    quantity = IntegerField('调拨数量', validators=[
        DataRequired(message='请输入调拨数量'),
        NumberRange(min=1, message='调拨数量必须大于0')
    ], description='调拨的数量')
    
    remark = TextAreaField('备注', validators=[
        Optional(),
        Length(max=500)
    ], description='调拨的备注信息')
    
    submit = SubmitField('调拨')
