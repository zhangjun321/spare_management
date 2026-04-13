import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Alert, Spinner, Badge } from 'react-bootstrap'
import { FaBrain, FaChartLine, FaLightbulb, FaExclamationCircle, FaSync } from 'react-icons/fa'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, LineElement, PointElement } from 'chart.js'
import { Doughnut, Line } from 'react-chartjs-2'
import { useUIStore } from '@/stores'
import { aiAnalysisService } from '@/services/warehouse'
import MainLayout from '@/layouts/MainLayout'
import Footer from '@/components/Footer'
import AnalysisCarousel from '@/components/AnalysisCarousel'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, LineElement, PointElement)

const Analysis = () => {
  const { setLoading } = useUIStore()
  const [loading, setLoadingLocal] = useState(false)
  const [analysisData, setAnalysisData] = useState(null)
  const [error, setError] = useState(null)

  const loadAnalysis = async () => {
    try {
      setLoadingLocal(true)
      setLoading(true)
      setError(null)
      
      const response = await aiAnalysisService.getInventoryAnalysis(30)
      
      if (response.success) {
        setAnalysisData(response.data)
      } else {
        setError(response.error || '加载分析数据失败')
      }
    } catch (err) {
      console.error('加载分析数据失败:', err)
      setError('AI 分析服务暂时不可用，请稍后重试')
    } finally {
      setLoadingLocal(false)
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnalysis()
  }, [])

  const getRiskLevelColor = (level) => {
    const colorMap = {
      'low': 'success',
      'medium': 'warning',
      'high': 'danger',
      'critical': 'danger'
    }
    return colorMap[level] || 'secondary'
  }

  const getRiskLevelText = (level) => {
    const textMap = {
      'low': '低风险',
      'medium': '中风险',
      'high': '高风险',
      'critical': '严重风险'
    }
    return textMap[level] || level
  }

  // 库存周转率图表数据
  const turnoverChartData = {
    labels: analysisData?.turnoverTrend?.map(item => item.date) || [],
    datasets: [
      {
        label: '库存周转率',
        data: analysisData?.turnoverTrend?.map(item => item.turnoverRate) || [],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        tension: 0.4,
        fill: true,
      },
    ],
  }

  const turnoverChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      title: {
        display: true,
        text: '库存周转率趋势（近 30 天）',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  }

  // 库存分类图表数据
  const categoryChartData = {
    labels: analysisData?.categoryAnalysis?.map(item => item.category) || [],
    datasets: [
      {
        label: '库存金额',
        data: analysisData?.categoryAnalysis?.map(item => item.amount) || [],
        backgroundColor: [
          'rgba(255, 99, 132, 0.7)',
          'rgba(54, 162, 235, 0.7)',
          'rgba(255, 206, 86, 0.7)',
          'rgba(75, 192, 192, 0.7)',
          'rgba(153, 102, 255, 0.7)',
        ],
        borderColor: [
          'rgb(255, 99, 132)',
          'rgb(54, 162, 235)',
          'rgb(255, 206, 86)',
          'rgb(75, 192, 192)',
          'rgb(153, 102, 255)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const categoryChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
      title: {
        display: true,
        text: '库存分类占比',
      },
    },
  }

  return (
    <MainLayout showSidebar={true} showHeader={true}>
      <div className="position-relative" style={{ minHeight: 'calc(100vh - 120px)' }}>
        {/* 轮播图 */}
        <div className="container-fluid px-0 mb-4">
          <AnalysisCarousel />
        </div>

        {/* 页面头部 */}
        <Row className="mb-4">
          <Col>
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <h2 className="mb-0">
                  <FaBrain className="me-2 text-primary" />
                  AI 智能分析
                </h2>
                <p className="text-muted mb-0">基于 AI 的库存分析与智能建议</p>
              </div>
              <Button variant="outline-primary" onClick={loadAnalysis} disabled={loading}>
                <FaSync className={`me-2 ${loading ? 'spin' : ''}`} />
                刷新分析
              </Button>
            </div>
          </Col>
        </Row>

        {/* 错误提示 */}
        {error && (
          <Row className="mb-4">
            <Col>
              <Alert variant="danger">
                <FaExclamationCircle className="me-2" />
                {error}
              </Alert>
            </Col>
          </Row>
        )}

        {/* 加载中 */}
        {loading && !analysisData && (
          <Row className="justify-content-center">
            <Col xs="auto">
              <Spinner animation="border" role="status" variant="primary">
                <span className="visually-hidden">加载中...</span>
              </Spinner>
              <div className="mt-2 text-muted">正在分析库存数据...</div>
            </Col>
          </Row>
        )}

        {/* AI 洞察卡片 */}
        {analysisData && (
          <>
            <Row className="mb-4">
              <Col>
                <Card className="border-0 shadow-sm">
                  <Card.Header className="bg-white border-0 fw-bold py-3">
                    <FaLightbulb className="me-2 text-warning" />
                    AI 智能洞察
                  </Card.Header>
                  <Card.Body>
                    {analysisData.insights && analysisData.insights.length > 0 ? (
                      <div className="row">
                        {analysisData.insights.map((insight, index) => (
                          <div key={index} className="col-md-4 mb-3">
                            <Card className="border-0 h-100" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
                              <Card.Body>
                                <div className="d-flex align-items-start">
                                  <FaLightbulb className="me-3 mt-1" size={24} style={{ opacity: 0.8 }} />
                                  <div>
                                    <h6 className="mb-2">{insight.title}</h6>
                                    <p className="mb-0 small" style={{ opacity: 0.9 }}>{insight.description}</p>
                                  </div>
                                </div>
                              </Card.Body>
                            </Card>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <Alert variant="info" className="mb-0">
                        <FaLightbulb className="me-2" />
                        暂无 AI 洞察建议
                      </Alert>
                    )}
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            {/* 库存周转率分析 */}
            <Row className="mb-4">
              <Col md={8}>
                <Card className="border-0 shadow-sm">
                  <Card.Header className="bg-white border-0 fw-bold py-3">
                    <FaChartLine className="me-2 text-success" />
                    库存周转率分析
                  </Card.Header>
                  <Card.Body>
                    <div style={{ height: '300px' }}>
                      <Line data={turnoverChartData} options={turnoverChartOptions} />
                    </div>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={4}>
                <Card className="border-0 shadow-sm">
                  <Card.Header className="bg-white border-0 fw-bold py-3">
                    <FaBrain className="me-2 text-primary" />
                    关键指标
                  </Card.Header>
                  <Card.Body>
                    <div className="d-flex justify-content-between mb-3">
                      <div>
                        <div className="text-muted small">平均周转率</div>
                        <div className="h4 mb-0 text-primary">{analysisData.avgTurnoverRate?.toFixed(2) || '0.00'}</div>
                      </div>
                      <div>
                        <div className="text-muted small">周转天数</div>
                        <div className="h4 mb-0 text-success">{analysisData.turnoverDays || '0'} 天</div>
                      </div>
                    </div>
                    <hr />
                    <div className="mb-3">
                      <div className="text-muted small mb-2">库存健康度</div>
                      <div className="progress" style={{ height: '10px' }}>
                        <div 
                          className="progress-bar bg-success" 
                          role="progressbar"
                          style={{ width: `${analysisData.healthScore || 0}%` }}
                        />
                      </div>
                      <div className="text-end small text-muted mt-1">
                        {analysisData.healthScore || 0}%
                      </div>
                    </div>
                    <div className="text-center">
                      <Badge bg={getRiskLevelColor(analysisData.riskLevel)} pill>
                        {getRiskLevelText(analysisData.riskLevel)}
                      </Badge>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            {/* 库存分类分析 */}
            <Row className="mb-4">
              <Col md={6}>
                <Card className="border-0 shadow-sm">
                  <Card.Header className="bg-white border-0 fw-bold py-3">
                    <FaChartLine className="me-2 text-info" />
                    库存分类占比
                  </Card.Header>
                  <Card.Body>
                    <div style={{ height: '300px' }}>
                      <Doughnut data={categoryChartData} options={categoryChartOptions} />
                    </div>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={6}>
                <Card className="border-0 shadow-sm">
                  <Card.Header className="bg-white border-0 fw-bold py-3">
                    <FaExclamationCircle className="me-2 text-warning" />
                    风险预警
                  </Card.Header>
                  <Card.Body>
                    {analysisData.riskWarnings && analysisData.riskWarnings.length > 0 ? (
                      <div className="list-group list-group-flush">
                        {analysisData.riskWarnings.map((warning, index) => (
                          <div key={index} className="list-group-item px-0">
                            <div className="d-flex align-items-start">
                              <FaExclamationCircle className="me-2 mt-1 text-warning" />
                              <div className="flex-grow-1">
                                <div className="fw-bold mb-1">{warning.type}</div>
                                <div className="text-muted small mb-1">{warning.description}</div>
                                <div className="text-primary small">建议：{warning.suggestion}</div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <Alert variant="success" className="mb-0">
                        <FaLightbulb className="me-2" />
                        暂无风险预警，库存状况良好
                      </Alert>
                    )}
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </>
        )}
      </div>
      
      {/* Footer */}
      <Footer />
    </MainLayout>
  )
}

export default Analysis
