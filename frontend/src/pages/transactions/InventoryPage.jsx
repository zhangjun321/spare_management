import React from 'react'
import TransactionFormBase from './TransactionFormBase'

const InventoryPage = () => (
  <div className="p-3">
    <h4>盘点/差异处理</h4>
    <p className="text-muted">录入盘点差异，正差为入库，负差为出库。可与上传/算法对接后续扩展。</p>
    <TransactionFormBase txType="inventory_adjust" title="盘点调整单" requireSource />
  </div>
)

export default InventoryPage
