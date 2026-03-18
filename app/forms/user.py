from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models.user import User


class UserForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=50, message='用户名长度必须在 3-50 个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址'),
        Length(max=100, message='邮箱长度不能超过 100 个字符')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, max=128, message='密码长度必须在 6-128 个字符之间')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请再次输入密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    real_name = StringField('姓名', validators=[
        DataRequired(message='请输入姓名'),
        Length(max=50, message='姓名长度不能超过 50 个字符')
    ])
    phone = StringField('手机号', validators=[
        Optional(),
        Length(max=20, message='手机号长度不能超过 20 个字符')
    ])
    department_id = SelectField('部门', coerce=int, validators=[Optional()])
    role_id = SelectField('角色', coerce=int, validators=[
        DataRequired(message='请选择角色')
    ])
    is_admin = BooleanField('是否管理员', default=False)
    is_active = BooleanField('是否启用', default=True)
    remark = TextAreaField('备注', validators=[Optional()])
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        from app.models.department import Department
        from app.models.role import Role
        self.department_id.choices = [(0, '请选择部门')] + [
            (d.id, d.name) for d in Department.query.filter_by(is_active=True).order_by(Department.name).all()
        ]
        self.role_id.choices = [
            (r.id, r.name) for r in Role.query.filter_by(is_active=True).order_by(Role.name).all()
        ]
    
    def validate_username(self, field):
        if self.id:
            user = User.query.filter_by(username=field.data).first()
            if user and user.id != self.id:
                raise ValidationError('该用户名已存在')
        else:
            if User.query.filter_by(username=field.data).first():
                raise ValidationError('该用户名已存在')
    
    def validate_email(self, field):
        if self.id:
            user = User.query.filter_by(email=field.data).first()
            if user and user.id != self.id:
                raise ValidationError('该邮箱已被使用')
        else:
            if User.query.filter_by(email=field.data).first():
                raise ValidationError('该邮箱已被使用')


class UserProfileForm(FlaskForm):
    real_name = StringField('姓名', validators=[
        DataRequired(message='请输入姓名'),
        Length(max=50, message='姓名长度不能超过 50 个字符')
    ])
    phone = StringField('手机号', validators=[
        Optional(),
        Length(max=20, message='手机号长度不能超过 20 个字符')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址'),
        Length(max=100, message='邮箱长度不能超过 100 个字符')
    ])
    department_id = SelectField('部门', coerce=int, validators=[Optional()])
    remark = TextAreaField('备注', validators=[Optional()])
    submit = SubmitField('保存')
    
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        from app.models.department import Department
        self.department_id.choices = [(0, '请选择部门')] + [
            (d.id, d.name) for d in Department.query.filter_by(is_active=True).order_by(Department.name).all()
        ]


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('当前密码', validators=[
        DataRequired(message='请输入当前密码')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(min=6, max=128, message='密码长度必须在 6-128 个字符之间')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请再次输入新密码'),
        EqualTo('new_password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('修改密码')
