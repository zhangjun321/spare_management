"""
交易管理模块路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.forms.transaction import TransferForm, TransactionForm
from app.services.transaction_service import TransactionService
from app.models.batch import Batch
from app.utils.decorators import permission_required
from app.utils.helpers import paginate_query

transactions_bp = Blueprint('transactions', __name__, template_folder='../templates/transactions')


@transactions_bp.route('/')
@login_required
def index():
    """交易列表"""
    return render_template('transactions/index.html')


@transactions_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
@permission_required('transaction', 'create')
def transfer():
    """备件调拨"""
    form = TransferForm()
    
    if form.validate_on_submit():
        try:
            data = {
                'from_warehouse_id': form.from_warehouse_id.data,
                'to_warehouse_id': form.to_warehouse_id.data,
                'spare_part_id': form.spare_part_id.data,
                'batch_id': form.batch_id.data,
                'quantity': form.quantity.data,
                'remark': form.remark.data
            }
            
            out_transaction, in_transaction = TransactionService.transfer_spare_part(data, current_user.id)
            
            flash('调拨成功！', 'success')
            return redirect(url_for('transactions.index'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'调拨失败：{str(e)}', 'danger')
    
    return render_template('transactions/transfer.html', form=form)


@transactions_bp.route('/get-batches/<int:spare_part_id>')
@login_required
def get_batches(spare_part_id):
    """获取备件的批次列表"""
    batches = Batch.query.filter_by(spare_part_id=spare_part_id, status='active').all()
    batch_options = [(0, '请选择批次')] + [(b.id, b.batch_number) for b in batches]
    return jsonify(batch_options)


@transactions_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('transaction', 'create')
def create():
    """创建交易"""
    form = TransactionForm()
    
    if form.validate_on_submit():
        try:
            data = {
                'transaction_type': form.transaction_type.data,
                'warehouse_id': form.warehouse_id.data,
                'spare_part_id': form.spare_part_id.data,
                'batch_id': form.batch_id.data,
                'quantity': form.quantity.data,
                'unit_price': form.unit_price.data,
                'remark': form.remark.data
            }
            
            transaction = TransactionService.create_transaction(data, current_user.id)
            
            flash('交易创建成功，等待审批！', 'success')
            return redirect(url_for('transactions.index'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'交易创建失败：{str(e)}', 'danger')
    
    return render_template('transactions/create.html', form=form)


@transactions_bp.route('/approve/<int:transaction_id>', methods=['POST'])
@login_required
@permission_required('transaction', 'update')
def approve(transaction_id):
    """审批交易"""
    try:
        if request.form.get('transaction_type') in ['transfer_out', 'transfer_in']:
            transaction = TransactionService.approve_transfer_transaction(transaction_id, current_user.id)
        else:
            transaction = TransactionService.approve_transaction(transaction_id, current_user.id)
        flash('交易审批成功！', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'审批失败：{str(e)}', 'danger')
    return redirect(url_for('transactions.index'))


@transactions_bp.route('/reject/<int:transaction_id>', methods=['POST'])
@login_required
@permission_required('transaction', 'update')
def reject(transaction_id):
    """拒绝交易"""
    reason = request.form.get('reason', '')
    try:
        transaction = TransactionService.reject_transaction(transaction_id, current_user.id, reason)
        flash('交易已拒绝！', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash(f'操作失败：{str(e)}', 'danger')
    return redirect(url_for('transactions.index'))

