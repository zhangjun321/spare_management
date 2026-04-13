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
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App
