import React, { useEffect, useState, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Card, Form, Button, Row, Col, Alert, Spinner, Badge, Modal,
} from 'react-bootstrap'
import SparePartService, { SparePartImageService, SparePartAIService } from '../services/sparePart'
import useSparePartStore from '../stores/sparePartStore'

const IMAGE_TYPES = [
  { type: 'front',       name: '正面图' },
  { type: 'side',        name: '侧面图' },
  { type: 'detail',      name: '详细图' },
  { type: 'circuit',     name: '电路图' },
  { type: 'perspective', name: '透视图' },
  { type: 'thumbnail',   name: '缩略图' },
]

const EMPTY_FORM = {
  part_code: '', name: '', specification: '', unit: '',
  category_id: '', supplier_id: '', warehouse_id: '', location_id: '',
  location: '', brand: '', barcode: '', currency: 'CNY',
  safety_stock: '', reorder_point: '', warranty_period: '',
  last_purchase_price: '', last_purchase_date: '', datasheet_url: '',
  current_stock: 0, min_stock: 0, max_stock: 0,
  unit_price: '', image_url: '', is_active: true, remark: '',
}

export default function SparePartForm() {
  const { id }  = useParams()
  const isEdit  = Boolean(id)
  const navigate = useNavigate()
  const { fetchOptions } = useSparePartStore()

  const [formData, setFormData]   = useState(EMPTY_FORM)
  const [options, setOptions]     = useState({ categories: [], suppliers: [], warehouses: [], locations: [] })
  const [images, setImages]       = useState({}) // { type: url }
  const [loading, setLoading]     = useState(false)
  const [saving, setSaving]       = useState(false)
  const [errors, setErrors]       = useState({})
  const [alertMsg, setAlertMsg]   = useState(null)

  // AI 填充 Modal
  const [aiModal, setAiModal]     = useState({ open: false, loading: false, result: null, error: null })
  const [aiApplied, setAiApplied] = useState(false)

  const fileInputs = useRef({})

  // ── 初始化 ──────────────────────────────────────────────
  useEffect(() => {
    const init = async () => {
      setLoading(true)
      try {
        const opts = await fetchOptions()
        if (opts) setOptions(opts)
        if (isEdit) {
          const res = await SparePartService.get(id)
          if (res.success) {
            const p = res.data
            setFormData({
              part_code: p.part_code || '',
              name: p.name || '',
              specification: p.specification || '',
              unit: p.unit || '',
              category_id: p.category_id || '',
              supplier_id: p.supplier_id || '',
              warehouse_id: p.warehouse_id || '',
              location_id: p.location_id || '',
              location: p.location || '',
              brand: p.brand || '',
              barcode: p.barcode || '',
              currency: p.currency || 'CNY',
              safety_stock: p.safety_stock ?? '',
              reorder_point: p.reorder_point ?? '',
              warranty_period: p.warranty_period || '',
              last_purchase_price: p.last_purchase_price ?? '',
              last_purchase_date: p.last_purchase_date || '',
              datasheet_url: p.datasheet_url || '',
              current_stock: p.current_stock ?? 0,
              min_stock: p.min_stock ?? 0,
              max_stock: p.max_stock ?? 0,
              unit_price: p.unit_price ?? '',
              image_url: p.image_url || '',
              is_active: p.is_active !== false,
              remark: p.remark || '',
            })
            // 加载图片
            const imgRes = await SparePartImageService.getImages(id)
            if (imgRes.success) {
              const imgMap = {}
              imgRes.images?.forEach(img => { imgMap[img.image_type] = img.url })
              setImages(imgMap)
            }
          }
        }
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [id])

  const showAlert = (type, msg) => {
    setAlertMsg({ type, msg })
    setTimeout(() => setAlertMsg(null), 4000)
  }

  // ── 表单变更 ─────────────────────────────────────────────
  const handleChange = (key, val) => {
    setFormData(prev => ({ ...prev, [key]: val }))
    if (errors[key]) setErrors(prev => { const e = { ...prev }; delete e[key]; return e })
  }

  // ── 校验 ─────────────────────────────────────────────────
  const validate = () => {
    const e = {}
    if (!formData.part_code.trim()) e.part_code = '备件代码不能为空'
    if (!formData.name.trim())      e.name = '名称不能为空'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  // ── 提交 ─────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setSaving(true)
    try {
      const payload = { ...formData }
      const res = isEdit
        ? await SparePartService.update(id, payload)
        : await SparePartService.create(payload)
      if (res.success) {
        showAlert('success', isEdit ? '保存成功！' : '新增成功！')
        setTimeout(() => navigate(`/spare_parts/${res.data?.id || id}`), 1200)
      } else {
        showAlert('danger', res.error || '保存失败')
      }
    } catch (err) {
      showAlert('danger', err.message)
    } finally {
      setSaving(false)
    }
  }

  // ── 图片上传 ─────────────────────────────────────────────
  const uploadImage = async (imageType) => {
    if (!isEdit) { showAlert('warning', '请先保存备件后再上传图片'); return }
    const file = fileInputs.current[imageType]?.files?.[0]
    if (!file) return
    try {
      const res = await SparePartImageService.uploadImage(id, imageType, file)
      if (res.success) {
        setImages(prev => ({ ...prev, [imageType]: res.url }))
        showAlert('success', `${IMAGE_TYPES.find(t => t.type === imageType)?.name}上传成功`)
      } else {
        showAlert('danger', res.error || '上传失败')
      }
    } catch (err) {
      showAlert('danger', err.message)
    }
  }

  const removeImage = async (imageType) => {
    if (!isEdit) return
    if (!window.confirm('确定要删除这张图片吗？')) return
    try {
      const res = await SparePartImageService.removeImage(id, imageType)
      if (res.success) {
        setImages(prev => { const n = { ...prev }; delete n[imageType]; return n })
        showAlert('success', '图片已删除')
      } else {
        showAlert('danger', res.error || '删除失败')
      }
    } catch (err) {
      showAlert('danger', err.message)
    }
  }

  // ── AI 填充 ───────────────────────────────────────────────
  const handleAiFill = async () => {
    if (!isEdit) { showAlert('warning', '请先保存备件后再使用AI填充'); return }
    setAiModal({ open: true, loading: true, result: null, error: null })
    try {
      const res = await SparePartAIService.fill(id)
      if (res.success) {
        setAiModal({ open: true, loading: false, result: res, error: null })
      } else {
        setAiModal({ open: true, loading: false, result: null, error: res.error || 'AI填充失败' })
      }
    } catch (err) {
      setAiModal({ open: true, loading: false, result: null, error: err.message })
    }
  }

  const applyAiFill = async () => {
    if (!aiModal.result?.filled_data) return
    try {
      const res = await SparePartAIService.applyFill(id, aiModal.result.filled_data)
      if (res.success) {
        setAiModal(prev => ({ ...prev, open: false }))
        showAlert('success', 'AI建议已应用！')
        setAiApplied(true)
        // 重新加载表单数据
        const detail = await SparePartService.get(id)
        if (detail.success) {
          const p = detail.data
          setFormData(prev => ({
            ...prev,
            specification: p.specification || prev.specification,
            unit_price: p.unit_price ?? prev.unit_price,
            remark: p.remark || prev.remark,
          }))
        }
      }
    } catch (err) {
      showAlert('danger', err.message)
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

  const title = isEdit ? `编辑备件 - ${formData.name || id}` : '新增备件'

  return (
    <div>
      {alertMsg && (
        <Alert variant={alertMsg.type} dismissible onClose={() => setAlertMsg(null)} className="mb-3">
          {alertMsg.msg}
        </Alert>
      )}

      <Card className="shadow-sm">
        <Card.Header className="bg-white">
          <h5 className="mb-0">{title}</h5>
        </Card.Header>
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            {/* 基本信息 */}
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>备件代码 <span className="text-danger">*</span></Form.Label>
                  <Form.Control
                    value={formData.part_code}
                    onChange={e => handleChange('part_code', e.target.value)}
                    isInvalid={!!errors.part_code}
                    required
                  />
                  <Form.Control.Feedback type="invalid">{errors.part_code}</Form.Control.Feedback>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>名称 <span className="text-danger">*</span></Form.Label>
                  <Form.Control
                    value={formData.name}
                    onChange={e => handleChange('name', e.target.value)}
                    isInvalid={!!errors.name}
                    required
                  />
                  <Form.Control.Feedback type="invalid">{errors.name}</Form.Control.Feedback>
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>规格型号</Form.Label>
                  <Form.Control value={formData.specification} onChange={e => handleChange('specification', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>单位</Form.Label>
                  <Form.Control value={formData.unit} onChange={e => handleChange('unit', e.target.value)} />
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>分类</Form.Label>
                  <Form.Select value={formData.category_id} onChange={e => handleChange('category_id', e.target.value)}>
                    <option value="">-- 选择分类 --</option>
                    {options.categories?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>供应商</Form.Label>
                  <Form.Select value={formData.supplier_id} onChange={e => handleChange('supplier_id', e.target.value)}>
                    <option value="">-- 选择供应商 --</option>
                    {options.suppliers?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>默认仓库</Form.Label>
                  <Form.Select value={formData.warehouse_id} onChange={e => handleChange('warehouse_id', e.target.value)}>
                    <option value="">-- 选择仓库 --</option>
                    {options.warehouses?.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>货位</Form.Label>
                  <Form.Select value={formData.location_id} onChange={e => handleChange('location_id', e.target.value)}>
                    <option value="">-- 选择货位 --</option>
                    {options.locations?.map(l => <option key={l.id} value={l.id}>{l.location_code}</option>)}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={12}>
                <Form.Group className="mb-3">
                  <Form.Label>存放位置</Form.Label>
                  <Form.Control value={formData.location} onChange={e => handleChange('location', e.target.value)} />
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>品牌</Form.Label>
                  <Form.Control value={formData.brand} onChange={e => handleChange('brand', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>条形码</Form.Label>
                  <Form.Control value={formData.barcode} onChange={e => handleChange('barcode', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>货币</Form.Label>
                  <Form.Select value={formData.currency} onChange={e => handleChange('currency', e.target.value)}>
                    <option value="CNY">CNY - 人民币</option>
                    <option value="USD">USD - 美元</option>
                    <option value="EUR">EUR - 欧元</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>安全库存</Form.Label>
                  <Form.Control type="number" value={formData.safety_stock} onChange={e => handleChange('safety_stock', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>再订购点</Form.Label>
                  <Form.Control type="number" value={formData.reorder_point} onChange={e => handleChange('reorder_point', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>保修期(月)</Form.Label>
                  <Form.Control type="number" value={formData.warranty_period} onChange={e => handleChange('warranty_period', e.target.value)} />
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>最后采购价</Form.Label>
                  <Form.Control type="number" step="0.01" value={formData.last_purchase_price} onChange={e => handleChange('last_purchase_price', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>最后采购日期</Form.Label>
                  <Form.Control type="date" value={formData.last_purchase_date} onChange={e => handleChange('last_purchase_date', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>数据表链接</Form.Label>
                  <Form.Control value={formData.datasheet_url} onChange={e => handleChange('datasheet_url', e.target.value)} />
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>当前库存</Form.Label>
                  <Form.Control type="number" value={formData.current_stock} onChange={e => handleChange('current_stock', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>最低库存</Form.Label>
                  <Form.Control type="number" value={formData.min_stock} onChange={e => handleChange('min_stock', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>最高库存</Form.Label>
                  <Form.Control type="number" value={formData.max_stock} onChange={e => handleChange('max_stock', e.target.value)} />
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>单价</Form.Label>
                  <Form.Control type="number" step="0.01" value={formData.unit_price} onChange={e => handleChange('unit_price', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>图片 URL</Form.Label>
                  <Form.Control value={formData.image_url} onChange={e => handleChange('image_url', e.target.value)} />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <div className="form-check mt-4">
                    <Form.Check
                      label="启用"
                      checked={formData.is_active}
                      onChange={e => handleChange('is_active', e.target.checked)}
                    />
                  </div>
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>备注</Form.Label>
              <Form.Control as="textarea" rows={3} value={formData.remark} onChange={e => handleChange('remark', e.target.value)} />
            </Form.Group>

            {/* 图片管理区域 */}
            <div className="mt-4">
              <Card className="border-0 bg-light">
                <Card.Header className="bg-white d-flex justify-content-between align-items-center">
                  <h5 className="mb-0"><i className="fas fa-images me-2" />备件图片管理</h5>
                  {isEdit && (
                    <Button variant="info" type="button" onClick={handleAiFill}>
                      <i className="fas fa-robot me-1" />AI智能填充
                    </Button>
                  )}
                </Card.Header>
                <Card.Body>
                  <Row id="imageGallery">
                    {IMAGE_TYPES.map(({ type, name }) => (
                      <Col md={4} sm={6} className="mb-3" key={type}>
                        <Card className="image-card">
                          <Card.Body className="text-center p-2">
                            <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa', borderRadius: 4 }}>
                              {images[type]
                                ? <img src={images[type]} alt={name} className="img-fluid" style={{ maxHeight: 180 }} />
                                : <div className="text-muted">
                                    <i className="fas fa-image fa-3x" />
                                    <p className="mt-2 mb-0">{name}</p>
                                  </div>}
                            </div>
                            <div className="mt-2 d-flex justify-content-center gap-2">
                              <input
                                type="file"
                                accept="image/*"
                                style={{ display: 'none' }}
                                ref={el => fileInputs.current[type] = el}
                                onChange={() => uploadImage(type)}
                              />
                              <Button size="sm" variant="outline-primary" type="button"
                                onClick={() => fileInputs.current[type]?.click()}>
                                <i className="fas fa-upload" /> 上传
                              </Button>
                              {images[type] && (
                                <Button size="sm" variant="outline-danger" type="button"
                                  onClick={() => removeImage(type)}>
                                  <i className="fas fa-trash" /> 删除
                                </Button>
                              )}
                            </div>
                          </Card.Body>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Card.Body>
              </Card>
            </div>

            {/* 提交按钮 */}
            <div className="mt-4 d-flex gap-2">
              <Button type="submit" variant="primary" disabled={saving}>
                {saving ? <><Spinner size="sm" animation="border" className="me-1" />保存中...</> : <><i className="fas fa-save me-1" />保存</>}
              </Button>
              <Button type="button" variant="secondary" onClick={() => navigate(-1)}>
                <i className="fas fa-arrow-left me-1" />返回
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>

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
