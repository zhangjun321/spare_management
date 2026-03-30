from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, IntegerField, BooleanField, SubmitField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models.spare_part import SparePart
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation


class SparePartForm(FlaskForm):
    part_code = StringField('备件代码', validators=[
        DataRequired(message='请输入备件代码'),
        Length(max=50, message='备件代码长度不能超过 50 个字符')
    ])
    name = StringField('备件名称', validators=[
        DataRequired(message='请输入备件名称'),
        Length(max=200, message='备件名称长度不能超过 200 个字符')
    ])
    specification = StringField('规格型号', validators=[
        Length(max=200, message='规格型号长度不能超过 200 个字符')
    ])
    category_id = SelectField('分类', coerce=int, validators=[Optional()])
    supplier_id = SelectField('供应商', coerce=int, validators=[Optional()])
    warehouse_id = SelectField('默认仓库', coerce=int, validators=[Optional()])
    location_id = SelectField('默认货位', coerce=int, validators=[Optional()])
    current_stock = IntegerField('当前库存', default=0)
    min_stock = IntegerField('最低库存', default=0)
    max_stock = IntegerField('最高库存', validators=[Optional()])
    unit = StringField('单位', validators=[
        Length(max=20, message='单位长度不能超过 20 个字符')
    ])
    unit_price = DecimalField('单价', places=2, validators=[
        Optional(),
        NumberRange(min=0, message='单价必须大于等于 0')
    ])
    location = StringField('存放位置', validators=[
        Length(max=200, message='存放位置长度不能超过 200 个字符')
    ])
    brand = StringField('品牌', validators=[
        Length(max=100, message='品牌长度不能超过 100 个字符')
    ])
    barcode = StringField('条形码', validators=[
        Length(max=100, message='条形码长度不能超过 100 个字符')
    ])
    safety_stock = IntegerField('安全库存', default=0)
    reorder_point = IntegerField('再订货点', validators=[Optional()])
    last_purchase_price = DecimalField('最近采购价', places=2, validators=[
        Optional(),
        NumberRange(min=0, message='价格必须大于等于 0')
    ])
    currency = SelectField('币种', choices=[('CNY', '人民币'), ('USD', '美元'), ('EUR', '欧元'), ('JPY', '日元')], default='CNY')
    warranty_period = IntegerField('质保期 (月)', validators=[Optional()])
    last_purchase_date = DateTimeLocalField('最后采购日期', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    datasheet_url = StringField('数据手册 URL', validators=[
        Length(max=500, message='数据手册 URL 长度不能超过 500 个字符')
    ])
    image_url = StringField('图片 URL', validators=[
        Length(max=500, message='图片 URL 长度不能超过 500 个字符')
    ])
    remark = TextAreaField('备注', validators=[Optional()])
    is_active = BooleanField('是否启用', default=True)
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(SparePartForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(0, '请选择分类')] + [
            (c.id, c.name) for c in Category.query.filter_by(is_active=True).order_by(Category.name).all()
        ]
        self.supplier_id.choices = [(0, '请选择供应商')] + [
            (s.id, s.name) for s in Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
        ]
        self.warehouse_id.choices = [(0, '请选择仓库')] + [
            (w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).order_by(Warehouse.name).all()
        ]
        self.location_id.choices = [(0, '请选择货位')]
        # 如果提供了仓库ID，只显示该仓库的货位
        if 'warehouse_id' in kwargs and kwargs['warehouse_id']:
            self.location_id.choices += [
                (l.id, l.location_code) for l in WarehouseLocation.query.filter_by(
                    warehouse_id=kwargs['warehouse_id'], status='available'
                ).order_by(WarehouseLocation.location_code).all()
            ]
        else:
            self.location_id.choices += [
                (l.id, f"{l.warehouse.name}-{l.location_code}") for l in WarehouseLocation.query.filter_by(
                    status='available'
                ).order_by(WarehouseLocation.warehouse_id, WarehouseLocation.location_code).all()
            ]
    
    def validate_part_code(self, field):
        if self.id:
            spare_part = SparePart.query.filter_by(part_code=field.data).first()
            if spare_part and spare_part.id != self.id:
                raise ValidationError('该备件代码已存在')
        else:
            if SparePart.query.filter_by(part_code=field.data).first():
                raise ValidationError('该备件代码已存在')


class SparePartSearchForm(FlaskForm):
    keyword = StringField('搜索关键词', validators=[Optional()])
    category_id = SelectField('分类', coerce=int, validators=[Optional()])
    supplier_id = SelectField('供应商', coerce=int, validators=[Optional()])
    stock_status = SelectField('库存状态', coerce=str, validators=[Optional()], 
                               choices=[('', '全部'), ('normal', '正常'), ('low', '不足'), ('overstocked', '过剩')])
    is_active = SelectField('状态', coerce=str, validators=[Optional()],
                           choices=[('', '全部'), ('1', '启用'), ('0', '停用')])
    submit = SubmitField('搜索')
    
    def __init__(self, *args, **kwargs):
        super(SparePartSearchForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(0, '全部分类')] + [
            (c.id, c.name) for c in Category.query.filter_by(is_active=True).order_by(Category.name).all()
        ]
        self.supplier_id.choices = [(0, '全部供应商')] + [
            (s.id, s.name) for s in Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
        ]
