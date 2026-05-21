import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import InboundList from './pages/InboundList'
import OutboundList from './pages/OutboundList'
import InventoryList from './pages/InventoryList'
import Analysis from './pages/Analysis'
import WarehouseList from './pages/WarehouseList'
import WarehouseDetail from './pages/WarehouseDetail'
import WarehouseForm from './pages/WarehouseForm'
import SparePartList from './pages/SparePartList'
import SparePartDetail from './pages/SparePartDetail'
import SparePartForm from './pages/SparePartForm'
import TransactionList from './pages/transactions/TransactionList'
import InboundPage from './pages/transactions/InboundPage'
import OutboundPage from './pages/transactions/OutboundPage'
import TransferPage from './pages/transactions/TransferPage'
import InventoryPage from './pages/transactions/InventoryPage'
// Phase 2: 新业务模块页面
import TransferOrderList from './pages/TransferOrderList'
import TransferOrderForm from './pages/TransferOrderForm'
import TransferOrderDetail from './pages/TransferOrderDetail'
import ReservationList from './pages/ReservationList'
import ReservationForm from './pages/ReservationForm'
import ReservationDetail from './pages/ReservationDetail'
import StockTakeList from './pages/StockTakeList'
import StockTakeNew from './pages/StockTakeNew'
import StockTakeDetail from './pages/StockTakeDetail'
import StockTakeExecute from './pages/StockTakeExecute'
import AdjustmentsList from './pages/AdjustmentsList'

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/warehouse/warehouses" replace />} />
          <Route path="/warehouse/dashboard" element={<Dashboard />} />
          <Route path="/warehouse/inbound" element={<InboundList />} />
          <Route path="/warehouse/outbound" element={<OutboundList />} />
          <Route path="/warehouse/inventory" element={<InventoryList />} />
          <Route path="/warehouse/analysis" element={<Analysis />} />

          {/* 仓库管理路由 */}
          <Route path="/warehouse/warehouses" element={<WarehouseList />} />
          <Route path="/warehouse/warehouses/new" element={<WarehouseForm />} />
          <Route path="/warehouse/warehouses/:id" element={<WarehouseDetail />} />
          <Route path="/warehouse/warehouses/:id/edit" element={<WarehouseForm />} />

          {/* 交易管理路由 */}
          <Route path="/transactions/list" element={<TransactionList />} />
          <Route path="/transactions/inbound" element={<InboundPage />} />
          <Route path="/transactions/outbound" element={<OutboundPage />} />
          <Route path="/transactions/transfer" element={<TransferPage />} />
          <Route path="/transactions/inventory" element={<InventoryPage />} />
          {/* 交易管理路由 - 带 /react 前缀（后台模板直出时使用） */}
          <Route path="/react/transactions/list" element={<TransactionList />} />
          <Route path="/react/transactions/inbound" element={<InboundPage />} />
          <Route path="/react/transactions/outbound" element={<OutboundPage />} />
          <Route path="/react/transactions/transfer" element={<TransferPage />} />
          <Route path="/react/transactions/inventory" element={<InventoryPage />} />

          {/* 备件管理路由（直接访问 /spare-parts/...） */}
          <Route path="/spare-parts" element={<SparePartList />} />
          <Route path="/spare-parts/new" element={<SparePartForm />} />
          <Route path="/spare-parts/:id" element={<SparePartDetail />} />
          <Route path="/spare-parts/:id/edit" element={<SparePartForm />} />

          {/* 备件管理路由（通过 /spare-parts-react 前缀访问） */}
          <Route path="/spare-parts-react" element={<Navigate to="/spare-parts-react/spare-parts" replace />} />
          <Route path="/spare-parts-react/" element={<Navigate to="/spare-parts-react/spare-parts" replace />} />
          <Route path="/spare-parts-react/spare-parts" element={<SparePartList />} />
          <Route path="/spare-parts-react/spare-parts/new" element={<SparePartForm />} />
          <Route path="/spare-parts-react/spare-parts/:id" element={<SparePartDetail />} />
          <Route path="/spare-parts-react/spare-parts/:id/edit" element={<SparePartForm />} />

          {/* 备件管理路由（原始 /spare_parts/ URI，保持与旧系统 URL 完全一致） */}
          <Route path="/spare_parts" element={<SparePartList />} />
          <Route path="/spare_parts/" element={<SparePartList />} />
          <Route path="/spare_parts/new" element={<SparePartForm />} />
          <Route path="/spare_parts/:id" element={<SparePartDetail />} />
          <Route path="/spare_parts/:id/edit" element={<SparePartForm />} />

          {/* Phase 2: 调拨单管理 */}
          <Route path="/transfer-orders" element={<TransferOrderList />} />
          <Route path="/transfer-orders/new" element={<TransferOrderForm />} />
          <Route path="/transfer-orders/:id" element={<TransferOrderDetail />} />
          <Route path="/transfer-orders/:id/edit" element={<TransferOrderForm />} />

          {/* Phase 2: 库存预留管理 */}
          <Route path="/reservations" element={<ReservationList />} />
          <Route path="/reservations/new" element={<ReservationForm />} />
          <Route path="/reservations/:id" element={<ReservationDetail />} />

          {/* Phase 2: 盘点任务管理 */}
          <Route path="/stock-take" element={<StockTakeList />} />
          <Route path="/stock-take/new" element={<StockTakeNew />} />
          <Route path="/stock-take/:id" element={<StockTakeDetail />} />
          <Route path="/stock-take/:id/execute" element={<StockTakeExecute />} />
          <Route path="/stock-take/adjustments" element={<AdjustmentsList />} />
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App
