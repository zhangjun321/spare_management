from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional, Email, ValidationError
from app.models.supplier import Supplier


class SupplierForm(FlaskForm):
    name = StringField('供应商名称', validators=[
        DataRequired(message='请输入供应商名称'),
        Length(max=200, message='供应商名称长度不能超过 200 个字符')
    ])
    code = StringField('供应商代码', validators=[
        DataRequired(message='请输入供应商代码'),
        Length(max=50, message='供应商代码长度不能超过 50 个字符')
    ])
    contact_person = StringField('联系人', validators=[
        Optional(),
        Length(max=50, message='联系人长度不能超过 50 个字符')
    ])
    phone = StringField('联系电话', validators=[
        Optional(),
        Length(max=50, message='联系电话长度不能超过 50 个字符')
    ])
    email = StringField('邮箱', validators=[
        Optional(),
        Email(message='请输入有效的邮箱地址'),
        Length(max=100, message='邮箱长度不能超过 100 个字符')
    ])
    address = StringField('地址', validators=[
        Optional(),
        Length(max=500, message='地址长度不能超过 500 个字符')
    ])
    website = StringField('网站', validators=[
        Optional(),
        Length(max=200, message='网站长度不能超过 200 个字符')
    ])
    type = SelectField('供应商类型', choices=[
        ('manufacturer', '生产商'),
        ('distributor', '经销商'),
        ('service', '服务商'),
        ('other', '其他')
    ])
    level = SelectField('供应商等级', choices=[
        ('A', 'A 级'),
        ('B', 'B 级'),
        ('C', 'C 级'),
        ('D', 'D 级')
    ])
    rating = SelectField('评级', coerce=int, choices=[(i, f'{i}星') for i in range(1, 6)])
    remark = TextAreaField('备注', validators=[Optional()])
    is_active = BooleanField('是否启用', default=True)
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(SupplierForm, self).__init__(*args, **kwargs)
    
    def validate_code(self, field):
        if self.id:
            supplier = Supplier.query.filter_by(code=field.data).first()
            if supplier and supplier.id != self.id:
                raise ValidationError('该供应商代码已存在')
        else:
            if Supplier.query.filter_by(code=field.data).first():
                raise ValidationError('该供应商代码已存在')
