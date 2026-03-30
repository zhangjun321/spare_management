from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from app.models.warehouse import Warehouse
from app.models.spare_part import SparePart
from app.models.batch import Batch


class TransferForm(FlaskForm):
    """备件调拨表单"""
    from_warehouse_id = SelectField('调出仓库', coerce=int, validators=[DataRequired(message='请选择调出仓库')])
    to_warehouse_id = SelectField('调入仓库', coerce=int, validators=[DataRequired(message='请选择调入仓库')])
    spare_part_id = SelectField('备件', coerce=int, validators=[DataRequired(message='请选择备件')])
    batch_id = SelectField('批次', coerce=int, validators=[Optional()])
    quantity = IntegerField('调拨数量', validators=[
        DataRequired(message='请输入调拨数量'),
        NumberRange(min=1, message='调拨数量必须大于0')
    ])
    remark = TextAreaField('备注', validators=[Optional()])
    submit = SubmitField('确认调拨')
    
    def __init__(self, *args, **kwargs):
        super(TransferForm, self).__init__(*args, **kwargs)
        # 加载仓库选项
        self.from_warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).order_by(Warehouse.name).all()]
        self.to_warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).order_by(Warehouse.name).all()]
        # 加载备件选项
        self.spare_part_id.choices = [(p.id, f"{p.part_code} - {p.name}") for p in SparePart.query.filter_by(is_active=True).order_by(SparePart.part_code).all()]
        # 批次选项会在选择备件后通过AJAX加载
        self.batch_id.choices = [(0, '请先选择备件')]


class TransactionForm(FlaskForm):
    """交易表单"""
    transaction_type = SelectField('交易类型', coerce=str, validators=[DataRequired(message='请选择交易类型')],
                                 choices=[('in', '入库'), ('out', '出库'), ('adjust_in', '盘盈'), ('adjust_out', '盘亏')])
    warehouse_id = SelectField('仓库', coerce=int, validators=[DataRequired(message='请选择仓库')])
    spare_part_id = SelectField('备件', coerce=int, validators=[DataRequired(message='请选择备件')])
    batch_id = SelectField('批次', coerce=int, validators=[Optional()])
    quantity = IntegerField('数量', validators=[
        DataRequired(message='请输入数量'),
        NumberRange(min=1, message='数量必须大于0')
    ])
    unit_price = DecimalField('单价', places=2, validators=[Optional()])
    remark = TextAreaField('备注', validators=[Optional()])
    submit = SubmitField('确认')
    
    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        # 加载仓库选项
        self.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).order_by(Warehouse.name).all()]
        # 加载备件选项
        self.spare_part_id.choices = [(p.id, f"{p.part_code} - {p.name}") for p in SparePart.query.filter_by(is_active=True).order_by(SparePart.part_code).all()]
        # 批次选项会在选择备件后通过AJAX加载
        self.batch_id.choices = [(0, '请先选择备件')]
