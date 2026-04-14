import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Card, Row, Col, Button, Badge, Alert, Spinner, Modal, Table,
} from 'react-bootstrap'
import SparePartService, { SparePartImageService, SparePartAIService } from '../services/sparePart'
import useSparePartStore from '../stores/sparePartStore'

const STOCK_STATUS = {
  out:         { bg: 'danger',  text: '缺货' },
  low:         { bg: 'danger',  text: '不足' },
  overstocked: { bg: 'warning', text: '过剩' },
  normal:      { bg: 'success', text: '正常' },
}

const IMAGE_FIELDS = [
  { field: 'image_url',           name: '正面图' },
  { field: 'side_image_url',      name: '侧面图' },
  { field: 'detail_image_url',    name: '详细图' },
  { field: 'circuit_image_url',   name: '电路图' },
  { field: 'perspective_image_url', name: '透视图' },
  { field: 'thumbnail_url',       name: '缩略图' },
]

export default function SparePartDetail() {
  const { id }  = useParams()
  const navigate = useNavigate()
  const { deletePart } = useSparePartStore()

  const [part, setPart]           = useState(null)
  const [loading, setLoading]     = useState(true)
  const [alertMsg, setAlertMsg]   = useState(null)
  const [showDelete, setShowDelete] = useState(false)

  // AI Modal
  const [aiModal, setAiModal]     = useState({ open: false, loading: false, result: null, error: null })

  // 条形码状态
  const [barcodeLoading, setBarcodeLoading] = useState(false)

  // ── 初始化 ──────────────────────────────────────────────
  useEffect(() => {
    loadPart()
  }, [id])

  const loadPart = async () => {
    setLoading(true)
    try {
      const res = await SparePartService.get(id)
      if (res.success) setPart(res.data)
      else setAlertMsg({ type: 'danger', msg: res.error || '加载失败' })
    } catch (e) {
      setAlertMsg({ type: 'danger', msg: e.message })
    } finally {
      setLoading(false)
    }
  }

  const showAlert = (type, msg) => {
    setAlertMsg({ type, msg })
    setTimeout(() => setAlertMsg(null), 4000)
  }

  // ── 删除 ─────────────────────────────────────────────────
  const handleDelete = async () => {
    const res = await deletePart(id)
    setShowDelete(false)
    if (res.success) {
      navigate('/spare_parts')
    } else {
      showAlert('danger', res.error || '删除失败')
    }
  }

  // ── 生成条形码 ────────────────────────────────────────────
  const handleGenerateBarcode = async () => {
    setBarcodeLoading(true)
    try {
      const res = await SparePartImageService.generateBarcode(id)
      if (res.success) {
        showAlert('success', '条形码生成成功！')
        await loadPart()
      } else {
        showAlert('danger', res.error || '生成失败')
      }
    } catch (e) {
      showAlert('danger', e.message)
    } finally {
      setBarcodeLoading(false)
    }
  }

  // ── 打印条形码 ────────────────────────────────────────────
  const handlePrintBarcode = () => {
    window.print()
  }

  // ── AI 填充 ───────────────────────────────────────────────
  const handleAiFill = async () => {
    setAiModal({ open: true, loading: true, result: null, error: null })
    try {
      const res = await SparePartAIService.fill(id)
      if (res.success) {
        setAiModal({ open: true, loading: false, result: res, error: null })
      } else {
        setAiModal({ open: true, loading: false, result: null, error: res.error || 'AI填充失败' })
      }
    } catch (e) {
      setAiModal({ open: true, loading: false, result: null, error: e.message })
    }
  }

  const applyAiFill = async () => {
    if (!aiModal.result?.filled_data) return
    try {
      const res = await SparePartAIService.applyFill(id, aiModal.result.filled_data)
      if (res.success) {
        setAiModal(p => ({ ...p, open: false }))
        showAlert('success', 'AI建议已应用！')
        await loadPart()
      }
    } catch (e) {
      showAlert('danger', e.message)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3 text-muted">加载中...</p>
      </div>
    )
  }

  if (!part) return null

  const st = STOCK_STATUS[part.stock_status] || STOCK_STATUS.normal

  return (
    <div>
      {alertMsg && (
        <Alert variant={alertMsg.type} dismissible onClose={() => setAlertMsg(null)} className="mb-3">
          {alertMsg.msg}
        </Alert>
      )}

      <Card className="shadow-sm">
        <Card.Header className="bg-white d-flex justify-content-between align-items-center">
          <h5 className="mb-0">{part.name}</h5>
          <div className="d-flex gap-2">
            <Button variant="info" onClick={handleAiFill}>
              <i className="fas fa-robot me-1" />AI智能填充
            </Button>
            <Button variant="success" onClick={() => navigate(`/spare_parts/${id}/edit`)}>
              <i className="fas fa-edit me-1" />编辑
            </Button>
            <Button variant="secondary" onClick={() => navigate('/spare_parts')}>
              <i className="fas fa-arrow-left me-1" />返回
            </Button>
          </div>
        </Card.Header>

        <Card.Body>
          {/* 基本信息 + 库存信息 */}
          <Row>
            <Col md={6}>
              <h6 className="border-bottom pb-2 mb-3">基本信息</h6>
              <Table size="sm">
                <tbody>
                  <tr><th width="30%">备件代码:</th><td>{part.part_code}</td></tr>
                  <tr><th>备件名称:</th><td>{part.name}</td></tr>
                  <tr><th>规格型号:</th><td>{part.specification || '-'}</td></tr>
                  <tr><th>单位:</th><td>{part.unit || '-'}</td></tr>
                  <tr>
                    <th>状态:</th>
                    <td><Badge bg={part.is_active ? 'success' : 'secondary'}>{part.is_active ? '启用' : '停用'}</Badge></td>
                  </tr>
                </tbody>
              </Table>
            </Col>
            <Col md={6}>
              <h6 className="border-bottom pb-2 mb-3">库存信息</h6>
              <Table size="sm">
                <tbody>
                  <tr>
                    <th width="30%">当前库存:</th>
                    <td><Badge bg={st.bg}>{part.current_stock} {part.unit || ''}</Badge></td>
                  </tr>
                  <tr>
                    <th>库存状态:</th>
                    <td><Badge bg={st.bg}>{st.text}</Badge></td>
                  </tr>
                  <tr><th>最低库存:</th><td>{part.min_stock ?? '-'}</td></tr>
                  <tr><th>最高库存:</th><td>{part.max_stock ?? '-'}</td></tr>
                  <tr><th>存放位置:</th><td>{part.location || '-'}</td></tr>
                  <tr><th>默认仓库:</th><td>{part.warehouse_name || '-'}</td></tr>
                  <tr><th>默认货位:</th><td>{part.location_code || '-'}</td></tr>
                </tbody>
              </Table>
            </Col>
          </Row>

          {/* 分类供应商 + 价格信息 */}
          <Row className="mt-4">
            <Col md={6}>
              <h6 className="border-bottom pb-2 mb-3">分类与供应商</h6>
              <Table size="sm">
                <tbody>
                  <tr><th width="30%">分类:</th><td>{part.category_name || '-'}</td></tr>
                  <tr><th>供应商:</th><td>{part.supplier_name || '-'}</td></tr>
                  {part.brand && <tr><th>品牌:</th><td>{part.brand}</td></tr>}
                </tbody>
              </Table>
            </Col>
            <Col md={6}>
              <h6 className="border-bottom pb-2 mb-3">价格信息</h6>
              <Table size="sm">
                <tbody>
                  <tr><th width="30%">单价:</th><td>¥{(Number(part.unit_price) || 0).toFixed(2)}</td></tr>
                  {part.last_purchase_price && <tr><th>最后采购价:</th><td>¥{(Number(part.last_purchase_price) || 0).toFixed(2)}</td></tr>}
                  {part.last_purchase_date && <tr><th>最后采购日期:</th><td>{part.last_purchase_date}</td></tr>}
                </tbody>
              </Table>
            </Col>
          </Row>

          {/* 备注 */}
          {part.remark && (
            <Row className="mt-4">
              <Col>
                <h6 className="border-bottom pb-2 mb-3">备注</h6>
                <p className="text-muted">{part.remark}</p>
              </Col>
            </Row>
          )}

          {/* 备件图片 */}
          <Row className="mt-4">
            <Col>
              <h6 className="border-bottom pb-2 mb-3"><i className="fas fa-images me-1" />备件图片</h6>
              <Row>
                {IMAGE_FIELDS.map(({ field, name }) => (
                  <Col md={4} sm={6} className="mb-3" key={field}>
                    <Card>
                      <Card.Body className="text-center p-2">
                        <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa', borderRadius: 4 }}>
                          {part[field]
                            ? <img src={part[field]} alt={name} className="img-fluid" style={{ maxHeight: 180, maxWidth: '100%' }} />
                            : <div className="text-muted"><i className="fas fa-image fa-3x" /><p className="mt-2 mb-0">{name}</p></div>}
                        </div>
                        <div className="mt-2"><small className="text-muted">{name}</small></div>
                      </Card.Body>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Col>
          </Row>

          {/* 系统信息 */}
          <Row className="mt-4">
            <Col>
              <h6 className="border-bottom pb-2 mb-3">系统信息</h6>
              <Table size="sm">
                <tbody>
                  <tr>
                    <th width="15%">创建时间:</th>
                    <td>{part.created_at || '-'}</td>
                    <th width="15%">更新时间:</th>
                    <td>{part.updated_at || '-'}</td>
                  </tr>
                </tbody>
              </Table>
            </Col>
          </Row>

          {/* 条形码 */}
          <Row className="mt-4">
            <Col>
              <h6 className="border-bottom pb-2 mb-3"><i className="fas fa-barcode me-1" />条形码</h6>
              <Card>
                <Card.Body className="text-center" id="barcodeContainer">
                  <div style={{ minHeight: 120, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    {part.barcode ? (
                      <div id="barcodeDisplay">
                        <img
                          id="barcodeImage"
                          src={SparePartImageService.barcodeUrl(id)}
                          alt="条形码"
                          style={{ maxWidth: 300 }}
                        />
                        <p className="mt-2 mb-0 text-muted">{part.barcode}</p>
                      </div>
                    ) : (
                      <div className="text-muted">
                        <i className="fas fa-barcode fa-3x" />
                        <p className="mt-2 mb-0">暂无条形码</p>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 d-flex justify-content-center gap-2">
                    {!part.barcode && (
                      <Button variant="primary" onClick={handleGenerateBarcode} disabled={barcodeLoading}>
                        {barcodeLoading
                          ? <><Spinner size="sm" animation="border" className="me-1" />生成中...</>
                          : <><i className="fas fa-magic me-1" />生成条形码</>}
                      </Button>
                    )}
                    {part.barcode && (
                      <Button variant="success" onClick={handlePrintBarcode}>
                        <i className="fas fa-print me-1" />打印条形码
                      </Button>
                    )}
                    <Button variant="danger" onClick={() => setShowDelete(true)}>
                      <i className="fas fa-trash me-1" />删除备件
                    </Button>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* 条形码打印区域 */}
      <style>{`
        @media print {
          body * { visibility: hidden; }
          #barcodePrintArea, #barcodePrintArea * { visibility: visible; }
          #barcodePrintArea { position: absolute; left: 0; top: 0; width: 100%; padding: 20px; background: white; }
        }
      `}</style>
      <div id="barcodePrintArea" style={{ display: 'none' }}>
        <div style={{ textAlign: 'center', padding: 20, border: '2px dashed #ccc' }}>
          <h3 style={{ marginBottom: 10 }}>{part.name}</h3>
          <p style={{ marginBottom: 10 }}>备件代码: {part.part_code}</p>
          {part.barcode && (
            <>
              <img src={SparePartImageService.barcodeUrl(id)} alt="条形码" style={{ maxWidth: 300 }} />
              <p style={{ marginTop: 10, fontWeight: 'bold' }}>{part.barcode}</p>
            </>
          )}
        </div>
      </div>

      {/* 删除确认 Modal */}
      <Modal show={showDelete} onHide={() => setShowDelete(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>确认删除</Modal.Title>
        </Modal.Header>
        <Modal.Body>确定要删除备件「{part.name}」吗？此操作不可撤销。</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDelete(false)}>取消</Button>
          <Button variant="danger" onClick={handleDelete}>确定删除</Button>
        </Modal.Footer>
      </Modal>

      {/* AI 填充 Modal */}
      <Modal show={aiModal.open} onHide={() => setAiModal(p => ({ ...p, open: false }))} size="xl" centered>
        <Modal.Header closeButton>
          <Modal.Title><i className="fas fa-robot me-2" />AI智能填充建议</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {aiModal.loading && (
            <div className="text-center py-5">
              <Spinner animation="border" variant="primary" style={{ width: 48, height: 48 }} />
              <p className="mt-3">AI正在分析备件信息，请稍候...</p>
            </div>
          )}
          {aiModal.error && (
            <div className="text-center text-danger py-4">
              <i className="fas fa-exclamation-triangle fa-3x" />
              <p className="mt-3">AI填充失败：{aiModal.error}</p>
            </div>
          )}
          {aiModal.result && (
            <>
              <Alert variant="info">
                <h6><i className="fas fa-info-circle me-1" />AI分析结果</h6>
                <p className="mb-0">信心分：<strong>{aiModal.result.confidence || 'N/A'}</strong>/100</p>
                <p className="mb-0">{aiModal.result.summary || ''}</p>
              </Alert>
              <Row>
                {aiModal.result.filled_data?.specification && (
                  <Col md={6} className="mb-3">
                    <Card>
                      <Card.Header className="bg-light"><strong>规格型号</strong></Card.Header>
                      <Card.Body><p className="mb-0">{aiModal.result.filled_data.specification}</p></Card.Body>
                    </Card>
                  </Col>
                )}
                {aiModal.result.filled_data?.unit_price_suggest != null && (
                  <Col md={6} className="mb-3">
                    <Card>
                      <Card.Header className="bg-light"><strong>价格建议</strong></Card.Header>
                      <Card.Body>
                        <p className="mb-0">参考价格：<strong>¥{(parseFloat(aiModal.result.filled_data.unit_price_suggest) || 0).toFixed(2)}</strong></p>
                        {aiModal.result.filled_data.price_reason && <small className="text-muted">{aiModal.result.filled_data.price_reason}</small>}
                      </Card.Body>
                    </Card>
                  </Col>
                )}
                {aiModal.result.filled_data?.remark && (
                  <Col md={12} className="mb-3">
                    <Card>
                      <Card.Header className="bg-light"><strong>备注建议</strong></Card.Header>
                      <Card.Body><p className="mb-0">{aiModal.result.filled_data.remark}</p></Card.Body>
                    </Card>
                  </Col>
                )}
              </Row>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setAiModal(p => ({ ...p, open: false }))}>关闭</Button>
          {aiModal.result && (
            <Button variant="primary" onClick={applyAiFill}>
              <i className="fas fa-check me-1" />应用建议
            </Button>
          )}
        </Modal.Footer>
      </Modal>
    </div>
  )
}
