import React from 'react'
import TransactionFormBase from './TransactionFormBase'

const InboundPage = () => (
  <div className="p-3">
    <h4>创建入库单</h4>
    <p className="text-muted">录入目标仓库及明细，支持批次、库位、金额。</p>
    <TransactionFormBase txType="inbound" title="入库单" requireTarget />
  </div>
)

export default InboundPage
