import React from 'react'
import TransactionFormBase from './TransactionFormBase'

const OutboundPage = () => (
  <div className="p-3">
    <h4>创建出库单</h4>
    <p className="text-muted">选择来源仓库/库位，提交后审批扣减库存。</p>
    <TransactionFormBase txType="outbound" title="出库单" requireSource />
  </div>
)

export default OutboundPage
