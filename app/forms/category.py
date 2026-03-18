from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.category import Category


class CategoryForm(FlaskForm):
    name = StringField('分类名称', validators=[
        DataRequired(message='请输入分类名称'),
        Length(max=100, message='分类名称长度不能超过 100 个字符')
    ])
    code = StringField('分类代码', validators=[
        DataRequired(message='请输入分类代码'),
        Length(max=50, message='分类代码长度不能超过 50 个字符')
    ])
    parent_id = SelectField('上级分类', coerce=int, validators=[Optional()])
    description = TextAreaField('描述', validators=[Optional()])
    is_active = BooleanField('是否启用', default=True)
    sort_order = SelectField('排序', coerce=int, choices=[(i, i) for i in range(1, 101)], default=1)
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.parent_id.choices = [(0, '无上级分类')] + [
            (c.id, c.name) for c in Category.query.filter_by(is_active=True).order_by(Category.name).all()
        ]
    
    def validate_code(self, field):
        if self.id:
            category = Category.query.filter_by(code=field.data).first()
            if category and category.id != self.id:
                raise ValidationError('该分类代码已存在')
        else:
            if Category.query.filter_by(code=field.data).first():
                raise ValidationError('该分类代码已存在')
