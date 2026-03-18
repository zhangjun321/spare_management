from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models.spare_part import SparePart
from app.models.category import Category
from app.models.supplier import Supplier


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
