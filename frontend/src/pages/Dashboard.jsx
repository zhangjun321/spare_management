import React, { useState, useEffect, useRef } from 'react'
import { Row, Col, Card, Spinner, Alert, Table, Button, Badge } from 'react-bootstrap'
import { 
  FaDownload, 
  FaUpload, 
  FaBoxes, 
  FaExclamationTriangle, 
  FaBell, 
  FaBrain,
  FaChartPie,
  FaChartLine,
  FaWarehouse,
  FaSyncAlt,
  FaRedo
} from 'react-icons/fa'
import { Doughnut, Line, Radar, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { warehouseStatsService, aiAnalysisService, inboundOrderService, outboundOrderService } from '../services/warehouse'
import { useUIStore } from '../stores'
import MainLayout from '../layouts/MainLayout'
import Footer from '../components/Footer'
import WarehouseCarousel from '../components/WarehouseCarousel'

// 注册 Chart.js 组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

const Dashboard = () => {
  const { setLoading, loading } = useUIStore()
  const [stats, setStats] = useState({
    todayInbound: 0,
    todayOutbound: 0,
    totalItems: 0,
    lowStockCount: 0,
    outOfStockCount: 0,
    aiInsightsCount: 0
  })
  const [aiInsights, setAiInsights] = useState(null)
  const [pendingTasks, setPendingTasks] = useState([])

  // 加载数据
  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // 加载统计数据
      const statsData = await warehouseStatsService.getAllStats()
      setStats(statsData)
      
      // 加载 AI 洞察
      try {
        const analysisData = await aiAnalysisService.getInventoryAnalysis(30)
        if (analysisData.success && analysisData.data.analysis) {
          setAiInsights(analysisData.data.analysis)
        }
      } catch (error) {
        console.error('加载 AI 洞察失败:', error)
      }
      
      // 加载待处理任务
      const [inboundOrders, outboundOrders] = await Promise.all([
        inboundOrderService.getPendingOrders(),
        outboundOrderService.getPendingOrders()
      ])
      
      const tasks = [
        ...inboundOrders.map(item => ({
          type: '入库',
          order_no: item.order_no,
          spare_part_name: `备件 #${item.spare_part_id}`,
          warehouse_name: `仓库 #${item.warehouse_id}`,
          quantity: item.quantity,
          created_at: item.created_at,
          id: item.id
        })),
        ...outboundOrders.map(item => ({
          type: '出库',
          order_no: item.order_no,
          spare_part_name: `备件 #${item.spare_part_id}`,
          warehouse_name: `仓库 #${item.warehouse_id}`,
          quantity: item.quantity,
          created_at: item.created_at,
          id: item.id
        }))
      ]
      
      tasks.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      setPendingTasks(tasks.slice(0, 5))
      
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  // 刷新数据
  const handleRefresh = () => {
    loadDashboardData()
  }

  // 处理任务
  const handleTask = (task) => {
    if (window.confirm(`确定要处理${task.type}单 ${task.order_no} 吗？`)) {
      const path = task.type === '入库' 
        ? `/warehouse/inbound/${task.id}/complete`
        : `/warehouse/outbound/${task.id}/complete`
      window.location.href = path
    }
  }

  // 统计卡片配置
  const statCards = [
    {
      title: '今日入库单',
      value: stats.todayInbound,
      icon: <FaDownload size={40} opacity={0.3} />,
      gradient: 'linear-gradient(135deg, #00dbde 0%, #fc00ff 100%)',
      onClick: () => window.location.href = '/warehouse/inbound'
    },
    {
      title: '今日出库单',
      value: stats.todayOutbound,
      icon: <FaUpload size={40} opacity={0.3} />,
      gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      onClick: () => window.location.href = '/warehouse/outbound'
    },
    {
      title: '库存品种数',
      value: stats.totalItems,
      icon: <FaBoxes size={40} opacity={0.3} />,
      gradient: 'linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)',
      color: '#333',
      onClick: () => window.location.href = '/warehouse/inventory'
    },
    {
      title: '低库存预警',
      value: stats.lowStockCount,
      icon: <FaExclamationTriangle size={40} opacity={0.3} />,
      gradient: 'linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%)',
      onClick: () => window.location.href = '/warehouse/inventory?status=low'
    },
    {
      title: '缺货预警',
      value: stats.outOfStockCount,
      icon: <FaBell size={40} opacity={0.3} />,
      gradient: 'linear-gradient(135deg, #ff4757 0%, #ff3838 100%)',
      onClick: () => window.location.href = '/warehouse/inventory?status=out'
    },
    {
      title: 'AI 分析建议',
      value: stats.aiInsightsCount,
      icon: <FaBrain size={40} opacity={0.3} />,
      gradient: 'linear-gradient(135deg, #a55eea 0%, #8854d0 100%)',
      onClick: () => window.location.href = '/warehouse/analysis'
    }
  ]

  // 库存状态分布图数据
  const stockStatusData = {
    labels: ['正常', '低库存', '缺货'],
    datasets: [{
      data: [
        Math.max(0, stats.totalItems - stats.lowStockCount - stats.outOfStockCount),
        stats.lowStockCount,
        stats.outOfStockCount
      ],
      backgroundColor: ['#00dbde', '#ffd700', '#ff4757'],
      borderWidth: 0
    }]
  }

  // 出入库趋势图数据
  const trendData = {
    labels: ['7 天前', '6 天前', '5 天前', '4 天前', '3 天前', '2 天前', '今天'],
    datasets: [
      {
        label: '入库',
        data: [12, 15, 8, 20, 18, 25, stats.todayInbound],
        borderColor: '#00dbde',
        backgroundColor: 'rgba(0, 219, 222, 0.1)',
        tension: 0.4,
        fill: true
      },
      {
        label: '出库',
        data: [10, 12, 15, 18, 14, 20, stats.todayOutbound],
        borderColor: '#fc00ff',
        backgroundColor: 'rgba(252, 0, 255, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  }

  // 仓库利用率图数据
  const utilizationData = {
    labels: ['仓库 A', '仓库 B', '仓库 C', '仓库 D', '仓库 E'],
    datasets: [{
      label: '利用率 (%)',
      data: [85, 72, 90, 65, 78],
      backgroundColor: 'rgba(255, 215, 0, 0.2)',
      borderColor: '#ffd700',
      pointBackgroundColor: '#ffd700',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: '#ffd700'
    }]
  }

  // 库存周转图数据
  const turnoverData = {
    labels: ['1 月', '2 月', '3 月', '4 月', '5 月', '6 月'],
    datasets: [{
      label: '周转率',
      data: [4.5, 5.2, 4.8, 6.1, 5.5, 6.8],
      backgroundColor: 'rgba(165, 94, 234, 0.8)',
      borderColor: '#a55eea',
      borderWidth: 1,
      borderRadius: 5
    }]
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom',
      }
    }
  }

  if (loading) {
    return (
      <MainLayout showSidebar={true} showHeader={true}>
        <div className="text-center py-5">
          <Spinner animation="border" variant="primary" role="status" style={{ width: '3rem', height: '3rem' }}>
            <span className="visually-hidden">Loading...</span>
          </Spinner>
          <p className="mt-3">正在加载数据...</p>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout showSidebar={true} showHeader={true}>
      <div className="position-relative" style={{ minHeight: 'calc(100vh - 120px)' }}>
        {/* 轮播图 */}
        <div className="container-fluid px-0 mb-4">
          <WarehouseCarousel />
        </div>
        
        {/* 刷新按钮 */}
        <Button
          variant="primary"
          className="position-fixed"
          style={{
            bottom: '30px',
            right: '30px',
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            boxShadow: '0 5px 20px rgba(0,0,0,0.3)',
            zIndex: 1000,
            fontSize: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          onClick={handleRefresh}
        >
          <FaRedo />
        </Button>

        {/* 统计卡片 */}
        <Row className="mb-4">
          {statCards.map((card, index) => (
            <Col xl={4} md={6} key={index} className="mb-4">
              <Card
                className="border-0 shadow-sm h-100"
                style={{
                  background: card.gradient,
                  color: card.color || 'white',
                  cursor: 'pointer',
                  transition: 'transform 0.3s, box-shadow 0.3s'
                }}
                onClick={card.onClick}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-5px)'
                  e.currentTarget.style.boxShadow = '0 8px 30px rgba(0,0,0,0.15)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = ''
                  e.currentTarget.style.boxShadow = ''
                }}
              >
                <Card.Body className="position-relative">
                  <div className="position-absolute" style={{ right: '20px', top: '20px', opacity: 0.3 }}>
                    {card.icon}
                  </div>
                  <div style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '5px' }}>
                    {card.value}
                  </div>
                  <div style={{ fontSize: '1rem', opacity: 0.9 }}>
                    {card.title}
                  </div>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>

        {/* AI 智能洞察 */}
        {aiInsights && (
          <Row className="mb-4">
            <Col>
              <Card 
                className="border-0 shadow-sm"
                style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white'
                }}
              >
                <Card.Body>
                  <h5 className="mb-3">
                    <FaBrain className="me-2" />
                    AI 智能洞察
                  </h5>
                  <div>
                    <strong>库存总体评估：</strong>{aiInsights.text || '库存状态良好'}<br />
                    <strong>建议：</strong>
                    <ul>
                      <li>关注 {stats.lowStockCount} 个低库存备件，及时补货</li>
                      <li>处理 {stats.outOfStockCount} 个缺货备件，避免影响生产</li>
                      <li>今日入库{stats.todayInbound}单，出库{stats.todayOutbound}单，运营正常</li>
                    </ul>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {/* 图表区域 */}
        <Row className="mb-4">
          <Col lg={6}>
            <Card className="border-0 shadow-sm mb-4">
              <Card.Body>
                <h5 className="mb-3">
                  <FaChartPie className="me-2 text-primary" />
                  库存状态分布
                </h5>
                <Doughnut data={stockStatusData} options={chartOptions} height={200} />
              </Card.Body>
            </Card>
          </Col>
          <Col lg={6}>
            <Card className="border-0 shadow-sm mb-4">
              <Card.Body>
                <h5 className="mb-3">
                  <FaChartLine className="me-2 text-primary" />
                  出入库趋势（近 7 天）
                </h5>
                <Line data={trendData} options={chartOptions} height={200} />
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <Row className="mb-4">
          <Col lg={6}>
            <Card className="border-0 shadow-sm mb-4">
              <Card.Body>
                <h5 className="mb-3">
                  <FaWarehouse className="me-2 text-primary" />
                  仓库利用率
                </h5>
                <Radar data={utilizationData} options={chartOptions} height={200} />
              </Card.Body>
            </Card>
          </Col>
          <Col lg={6}>
            <Card className="border-0 shadow-sm mb-4">
              <Card.Body>
                <h5 className="mb-3">
                  <FaSyncAlt className="me-2 text-primary" />
                  库存周转分析
                </h5>
                <Bar data={turnoverData} options={chartOptions} height={200} />
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* 待处理任务 */}
        <Row>
          <Col>
            <Card className="border-0 shadow-sm">
              <Card.Body>
                <h5 className="mb-3">
                  <i className="fas fa-tasks me-2 text-primary"></i>
                  待处理任务
                </h5>
                <div className="table-responsive">
                  <Table hover>
                    <thead>
                      <tr>
                        <th>任务类型</th>
                        <th>单据号</th>
                        <th>备件名称</th>
                        <th>仓库</th>
                        <th>数量</th>
                        <th>创建时间</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendingTasks.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="text-center text-muted">
                            暂无待处理任务
                          </td>
                        </tr>
                      ) : (
                        pendingTasks.map((task, index) => (
                          <tr key={index}>
                            <td>
                              <Badge bg={task.type === '入库' ? 'success' : 'warning'}>
                                {task.type}
                              </Badge>
                            </td>
                            <td>{task.order_no}</td>
                            <td>{task.spare_part_name}</td>
                            <td>{task.warehouse_name}</td>
                            <td>{task.quantity}</td>
                            <td>
                              {new Date(task.created_at).toLocaleString('zh-CN', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </td>
                            <td>
                              <Button
                                size="sm"
                                variant="primary"
                                onClick={() => handleTask(task)}
                              >
                                <i className="fas fa-check"></i> 处理
                              </Button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </Table>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </div>
      
      {/* Footer */}
      <Footer />
    </MainLayout>
  )
}

export default Dashboard
