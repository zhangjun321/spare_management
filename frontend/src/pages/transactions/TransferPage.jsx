import React from 'react'
import TransactionFormBase from './TransactionFormBase'

const TransferPage = () => (
  <div className="p-3">
    <h4>调拨/移库单</h4>
    <p className="text-muted">同一单据内同时记录调出与调入，审批后写入双向库存流水。</p>
    <TransactionFormBase txType="transfer" title="调拨单" requireSource requireTarget />
  </div>
)

export default TransferPage
