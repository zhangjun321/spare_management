import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Carousel, Card, Form, InputGroup, Dropdown, Button, Table,
  Row, Col, Pagination, Badge, Modal, ProgressBar, ListGroup,
  Spinner, Alert,
} from 'react-bootstrap'
import useSparePartStore from '../stores/sparePartStore'
import SparePartService, { SparePartImageService } from '../services/sparePart'

// ── 库存状态配置 ──────────────────────────────────────────────
const STOCK_STATUS = {
  out:         { bg: 'danger',  text: '缺货',  icon: 'fa-times-circle' },
  low:         { bg: 'danger',  text: '不足',  icon: 'fa-exclamation-triangle' },
  overstocked: { bg: 'warning', text: '过剩',  icon: 'fa-exclamation-circle' },
  normal:      { bg: 'success', text: '正常',  icon: 'fa-check-circle' },
}

// 图片类型
const IMAGE_TYPES = [
  { type: 'front',       name: '正面图' },
  { type: 'side',        name: '侧面图' },
  { type: 'detail',      name: '详细图' },
  { type: 'circuit',     name: '电路图' },
  { type: 'perspective', name: '透视图' },
  { type: 'thumbnail',   name: '缩略图' },
]

// 可选列定义
const ALL_COLUMNS = [
  { key: 'thumbnail',     label: '缩略图' },
  { key: 'part_code',     label: '备件代码' },
  { key: 'name',          label: '名称' },
  { key: 'specification', label: '规格型号' },
  { key: 'category',      label: '分类' },
  { key: 'supplier',      label: '供应商' },
  { key: 'current_stock', label: '当前库存' },
  { key: 'stock_status',  label: '库存状态' },
  { key: 'unit_price',    label: '单价' },
  { key: 'unit',          label: '单位' },
  { key: 'warehouse',     label: '仓库' },
  { key: 'location',      label: '货位' },
  { key: 'is_active',     label: '状态' },
  { key: 'barcode',       label: '条形码' },
  { key: 'action',        label: '操作' },
]

// 轮播图数据
const CAROUSEL_ITEMS = [
  { img: '/static/images/carousel/spare_parts_01.jpg', title: '备件库存管理',   desc: '全面管理备件信息，实时掌握库存动态',       icon: 'fa-boxes' },
  { img: '/static/images/carousel/spare_parts_02.jpg', title: '科学分类体系',   desc: '多级分类管理，快速定位所需备件',           icon: 'fa-tags' },
  { img: '/static/images/carousel/spare_parts_03.jpg', title: '规范入库流程',   desc: '严格质检入库，确保备件品质',               icon: 'fa-dolly' },
  { img: '/static/images/carousel/spare_parts_04.jpg', title: '高效出库管理',   desc: '快速响应需求，精准配货出库',               icon: 'fa-truck-loading' },
  { img: '/static/images/carousel/spare_parts_05.jpg', title: '完整批次追溯',   desc: '一物一码，全生命周期可追溯',               icon: 'fa-barcode' },
  { img: '/static/images/carousel/spare_parts_06.jpg', title: '定期库存盘点',   desc: '账实相符，确保库存准确性',                 icon: 'fa-clipboard-check' },
]

export default function SparePartList() {
  const navigate = useNavigate()
  const {
    parts, pagination, filters, loading,
    setFilters, fetchParts, fetchOptions, deletePart, toggleStatus,
  } = useSparePartStore()

  const [options, setOptions]           = useState({ categories: [], suppliers: [], warehouses: [] })
  const [selectedIds, setSelectedIds]   = useState([])
  const [viewMode, setViewMode]         = useState(() => localStorage.getItem('sparePartsView') || 'table')
  const [visibleCols, setVisibleCols]   = useState(() => {
    const saved = localStorage.getItem('sparePartsColumns')
    return saved ? JSON.parse(saved) : ALL_COLUMNS.map(c => c.key)
  })
  const [tempCols, setTempCols]         = useState(visibleCols)
  const [showColDrop, setShowColDrop]   = useState(false)
  const [showExportDrop, setShowExportDrop] = useState(false)
  const [alertMsg, setAlertMsg]         = useState(null) // { type, msg }
  const [deleteConfirm, setDeleteConfirm] = useState(null) // id

  // 图片生成进度 Modal
  const [genModal, setGenModal] = useState({
    open: false, partId: null, items: [], progress: 0, status: '准备中...', done: false,
  })

  // 扫码枪缓冲
  const barcodeBuffer  = useRef('')
  const lastInputTime  = useRef(0)
  const barcodeInputRef = useRef(null)

  // ── 初始化 ──────────────────────────────────────────────
  useEffect(() => {
    fetchParts(1)
    fetchOptions().then(res => { if (res) setOptions(res) })
  }, [])

  // 全局扫码枪监听
  useEffect(() => {
    const handler = (e) => {
      if (document.activeElement === barcodeInputRef.current) return
      const now = Date.now()
      if (now - lastInputTime.current > 100) barcodeBuffer.current = ''
      lastInputTime.current = now
      if (e.key === 'Enter' && barcodeBuffer.current.length > 3) {
        handleBarcodeSearch(barcodeBuffer.current)
        barcodeBuffer.current = ''
        return
      }
      if (e.key.length === 1) barcodeBuffer.current += e.key
    }
    window.addEventListener('keypress', handler)
    return () => window.removeEventListener('keypress', handler)
  }, [])

  const showAlert = (type, msg) => {
    setAlertMsg({ type, msg })
    setTimeout(() => setAlertMsg(null), 3000)
  }

  // ── 搜索/筛选 ────────────────────────────────────────────
  const handleSearch = useCallback(() => fetchParts(1), [filters])

  const handleFilter = (key, val) => setFilters({ [key]: val })

  const handlePerPage = (e) => {
    setFilters({ per_page: Number(e.target.value) })
    setTimeout(() => fetchParts(1), 0)
  }

  const handlePageChange = (page) => fetchParts(page)

  // ── 条形码搜索 ───────────────────────────────────────────
  const handleBarcodeSearch = async (barcode) => {
    if (!barcode) return
    try {
      const res = await SparePartService.searchByBarcode(barcode)
      if (res.success && res.spare_part) {
        navigate(`/spare_parts/${res.spare_part.id}`)
      } else {
        showAlert('warning', '未找到对应备件！')
        if (barcodeInputRef.current) barcodeInputRef.current.value = ''
      }
    } catch (e) {
      showAlert('danger', '搜索失败：' + e.message)
    }
  }

  // ── 删除 ────────────────────────────────────────────────
  const handleDelete = async (id) => {
    const res = await deletePart(id)
    setDeleteConfirm(null)
    if (res.success) showAlert('success', '删除成功')
    else showAlert('danger', res.error || '删除失败')
  }

  // ── 切换状态 ─────────────────────────────────────────────
  const handleToggleStatus = async (id) => {
    const res = await toggleStatus(id)
    if (!res.success) showAlert('danger', '操作失败')
  }

  // ── 导出 ─────────────────────────────────────────────────
  const handleExport = (format) => {
    const params = {}
    if (selectedIds.length > 0) {
      params.ids = selectedIds.join(',')
    } else {
      if (filters.keyword)      params.keyword = filters.keyword
      if (filters.category_id)  params.category_id = filters.category_id
      if (filters.supplier_id)  params.supplier_id = filters.supplier_id
      if (filters.stock_status) params.stock_status = filters.stock_status
      if (filters.is_active !== undefined && filters.is_active !== '') params.is_active = filters.is_active
    }
    window.location.href = SparePartService.exportUrl(format, params)
    setShowExportDrop(false)
  }

  // ── 图片生成 ─────────────────────────────────────────────
  const handleGenerateImages = async (partId) => {
    const items = IMAGE_TYPES.map(t => ({ ...t, status: 'pending' }))
    setGenModal({ open: true, partId, items, progress: 0, status: '准备中...', done: false })
    let successCount = 0
    const updatedItems = [...items]
    for (let i = 0; i < IMAGE_TYPES.length; i++) {
      const imgType = IMAGE_TYPES[i]
      updatedItems[i] = { ...updatedItems[i], status: 'generating' }
      setGenModal(prev => ({ ...prev, items: [...updatedItems], status: `正在生成: ${imgType.name}` }))
      try {
        const res = await SparePartImageService.generateSingleImage(partId, imgType.type)
        updatedItems[i] = { ...updatedItems[i], status: res.success ? 'success' : 'error' }
        if (res.success) successCount++
      } catch {
        updatedItems[i] = { ...updatedItems[i], status: 'error' }
      }
      const progress = Math.round(((i + 1) / IMAGE_TYPES.length) * 100)
      setGenModal(prev => ({ ...prev, items: [...updatedItems], progress }))
    }
    const finalStatus = successCount === IMAGE_TYPES.length
      ? '全部生成完成！'
      : `生成完成，成功 ${successCount}/${IMAGE_TYPES.length} 张`
    setGenModal(prev => ({ ...prev, status: finalStatus, done: true }))
    if (successCount === IMAGE_TYPES.length) {
      setTimeout(() => {
        setGenModal(prev => ({ ...prev, open: false }))
        fetchParts(pagination.page)
      }, 1500)
    }
  }

  // ── 列显示 ───────────────────────────────────────────────
  const applyColSettings = () => {
    setVisibleCols(tempCols)
    localStorage.setItem('sparePartsColumns', JSON.stringify(tempCols))
    setShowColDrop(false)
  }
  const resetColSettings = () => setTempCols(ALL_COLUMNS.map(c => c.key))

  // ── 全选 ─────────────────────────────────────────────────
  const toggleSelectAll = (checked) => {
    setSelectedIds(checked ? parts.map(p => p.id) : [])
  }

  // ── 生成分页组件 ─────────────────────────────────────────
  const renderPagination = () => {
    const { page, pages, has_prev, has_next } = pagination
    if (pages <= 1) return null
    const items = []
    items.push(
      <Pagination.Prev key="prev" disabled={!has_prev} onClick={() => handlePageChange(page - 1)}>
        <i className="fas fa-chevron-left" />
      </Pagination.Prev>
    )
    // 生成页码：始终显示首尾，中间省略号
    const range = []
    for (let i = 1; i <= pages; i++) {
      if (i === 1 || i === pages || (i >= page - 2 && i <= page + 2)) range.push(i)
      else if (range[range.length - 1] !== '...') range.push('...')
    }
    range.forEach((p, idx) => {
      if (p === '...') {
        items.push(<Pagination.Ellipsis key={`e${idx}`} disabled />)
      } else {
        items.push(
          <Pagination.Item key={p} active={p === page} onClick={() => handlePageChange(p)}>
            {p}
          </Pagination.Item>
        )
      }
    })
    items.push(
      <Pagination.Next key="next" disabled={!has_next} onClick={() => handlePageChange(page + 1)}>
        <i className="fas fa-chevron-right" />
      </Pagination.Next>
    )
    return <Pagination className="justify-content-end mb-0">{items}</Pagination>
  }

  // ── 卡片视图 ─────────────────────────────────────────────
  const renderCardView = () => (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
        gap: '20px',
        padding: '4px',
      }}
    >
      {parts.map(part => {
        const st = STOCK_STATUS[part.stock_status] || STOCK_STATUS.normal
        return (
          <Card key={part.id} className="shadow-sm h-100" style={{ transition: 'transform 0.2s, box-shadow 0.2s', cursor: 'default' }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)' }}
            onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = '' }}>
            {/* 图片 */}
            <div style={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fa', borderRadius: '0.375rem 0.375rem 0 0' }}>
              {part.thumbnail_url
                ? <img src={part.thumbnail_url} alt={part.name} style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 8 }} />
                : <div style={{ textAlign: 'center', color: '#ccc' }}><i className="fas fa-image fa-3x" /></div>}
            </div>
            <Card.Body>
              {[
                ['备件代码', <a key="code" style={{ cursor: 'pointer', color: '#0d6efd' }} onClick={() => navigate(`/spare_parts/${part.id}`)}>{part.part_code}</a>],
                ['名称', part.name],
                ['规格型号', part.specification || '-'],
                ['分类', part.category_name || '-'],
                ['供应商', part.supplier_name || '-'],
                ['库存', <><i key="icon" className={`fas ${st.icon} text-${st.bg} me-1`} /><Badge bg={st.bg}>{part.current_stock}</Badge></>],
                ['状态', <Badge key="st" bg={st.bg}>{st.text}</Badge>],
                ['单价', part.unit_price != null ? `¥${Number(part.unit_price).toFixed(2)}` : '-'],
                ['启用', <Badge key="active" bg={part.is_active ? 'success' : 'secondary'} style={{ cursor: 'pointer' }} onClick={() => handleToggleStatus(part.id)}>{part.is_active ? '启用' : '停用'}</Badge>],
                ['条形码', part.barcode ? <Badge key="bar" bg="info">{part.barcode}</Badge> : <span className="text-muted">-</span>],
              ].map(([label, val]) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #f0f0f0', fontSize: 13 }}>
                  <span style={{ fontWeight: 600, color: '#666', marginRight: 10 }}>{label}：</span>
                  <span>{val}</span>
                </div>
              ))}
              <div className="d-flex justify-content-center gap-2 mt-3">
                <Button size="sm" variant="outline-info" title="生成图片" onClick={() => {
                  if (window.confirm('确定要生成该备件的图片吗？')) handleGenerateImages(part.id)
                }}><i className="fas fa-magic" /></Button>
                <Button size="sm" variant="outline-primary" title="查看详情" onClick={() => navigate(`/spare_parts/${part.id}`)}><i className="fas fa-eye" /></Button>
                <Button size="sm" variant="outline-success" title="编辑" onClick={() => navigate(`/spare_parts/${part.id}/edit`)}><i className="fas fa-edit" /></Button>
                <Button size="sm" variant="outline-danger" title="删除" onClick={() => setDeleteConfirm(part.id)}><i className="fas fa-trash" /></Button>
              </div>
            </Card.Body>
          </Card>
        )
      })}
    </div>
  )

  // ── 表格视图 ─────────────────────────────────────────────
  const renderTableView = () => (
    <div className="table-responsive" style={{ overflowX: 'auto', maxWidth: '100%' }}>
      <Table hover className="align-middle mb-0" id="partsTable">
        <thead className="table-light">
          <tr>
            <th style={{ width: 40 }}>
              <Form.Check
                checked={parts.length > 0 && selectedIds.length === parts.length}
                onChange={e => toggleSelectAll(e.target.checked)}
              />
            </th>
            {visibleCols.includes('thumbnail')     && <th>缩略图</th>}
            {visibleCols.includes('part_code')     && <th>备件代码</th>}
            {visibleCols.includes('name')          && <th>名称</th>}
            {visibleCols.includes('specification') && <th>规格型号</th>}
            {visibleCols.includes('category')      && <th>分类</th>}
            {visibleCols.includes('supplier')      && <th>供应商</th>}
            {visibleCols.includes('current_stock') && <th>当前库存</th>}
            {visibleCols.includes('stock_status')  && <th>库存状态</th>}
            {visibleCols.includes('unit_price')    && <th>单价</th>}
            {visibleCols.includes('unit')          && <th>单位</th>}
            {visibleCols.includes('warehouse')     && <th>仓库</th>}
            {visibleCols.includes('location')      && <th>货位</th>}
            {visibleCols.includes('is_active')     && <th>状态</th>}
            {visibleCols.includes('barcode')       && <th>条形码</th>}
            {visibleCols.includes('action')        && <th>操作</th>}
          </tr>
        </thead>
        <tbody>
          {parts.length === 0 ? (
            <tr>
              <td colSpan={16} className="text-center text-muted py-4">
                {loading ? <Spinner animation="border" size="sm" /> : '暂无备件数据'}
              </td>
            </tr>
          ) : parts.map(part => {
            const st = STOCK_STATUS[part.stock_status] || STOCK_STATUS.normal
            return (
              <tr key={part.id}>
                <td>
                  <Form.Check
                    checked={selectedIds.includes(part.id)}
                    onChange={e => setSelectedIds(prev =>
                      e.target.checked ? [...prev, part.id] : prev.filter(i => i !== part.id)
                    )}
                  />
                </td>
                {visibleCols.includes('thumbnail') && (
                  <td className="text-center">
                    {part.thumbnail_url || part.image_url
                      ? <img src={part.thumbnail_url || part.image_url} alt={part.name}
                          style={{ width: 60, height: 60, objectFit: 'cover', borderRadius: 4 }} />
                      : <div style={{ width: 60, height: 60, background: '#f0f0f0', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <i className="fas fa-image" style={{ color: '#ccc' }} />
                        </div>}
                  </td>
                )}
                {visibleCols.includes('part_code')     && <td><a style={{ cursor: 'pointer', color: '#0d6efd', textDecoration: 'none' }} onClick={() => navigate(`/spare_parts/${part.id}`)}>{part.part_code}</a></td>}
                {visibleCols.includes('name')          && <td>{part.name}</td>}
                {visibleCols.includes('specification') && <td>{part.specification || '-'}</td>}
                {visibleCols.includes('category')      && <td>{part.category_name || '-'}</td>}
                {visibleCols.includes('supplier')      && <td>{part.supplier_name || '-'}</td>}
                {visibleCols.includes('current_stock') && (
                  <td>
                    <div className="d-flex align-items-center">
                      <i className={`fas ${st.icon} text-${st.bg} me-2`} />
                      <Badge bg={st.bg}>{part.current_stock}</Badge>
                    </div>
                  </td>
                )}
                {visibleCols.includes('stock_status') && (
                  <td><Badge bg={st.bg}>{st.text}</Badge></td>
                )}
                {visibleCols.includes('unit_price') && (
                  <td>¥{(Number(part.unit_price) || 0).toFixed(2)}</td>
                )}
                {visibleCols.includes('unit')      && <td>{part.unit || '-'}</td>}
                {visibleCols.includes('warehouse') && <td>{part.warehouse_name || '-'}</td>}
                {visibleCols.includes('location')  && <td>{part.location_code || '-'}</td>}
                {visibleCols.includes('is_active') && (
                  <td>
                    <Badge bg={part.is_active ? 'success' : 'secondary'} style={{ cursor: 'pointer' }}
                      onClick={() => handleToggleStatus(part.id)}>
                      {part.is_active ? '启用' : '停用'}
                    </Badge>
                  </td>
                )}
                {visibleCols.includes('barcode') && (
                  <td>
                    {part.barcode
                      ? <Badge bg="info">{part.barcode}</Badge>
                      : <span className="text-muted">-</span>}
                  </td>
                )}
                {visibleCols.includes('action') && (
                  <td>
                    <div className="btn-group btn-group-sm">
                      <Button variant="outline-info" size="sm" title="生成图片"
                        onClick={() => { if (window.confirm('确定要生成该备件的图片吗？')) handleGenerateImages(part.id) }}>
                        <i className="fas fa-magic" />
                      </Button>
                      <Button variant="outline-primary" size="sm" title="查看详情"
                        onClick={() => navigate(`/spare_parts/${part.id}`)}>
                        <i className="fas fa-eye" />
                      </Button>
                      <Button variant="outline-success" size="sm" title="编辑"
                        onClick={() => navigate(`/spare_parts/${part.id}/edit`)}>
                        <i className="fas fa-edit" />
                      </Button>
                      <Button variant="outline-danger" size="sm" title="删除"
                        onClick={() => setDeleteConfirm(part.id)}>
                        <i className="fas fa-trash" />
                      </Button>
                    </div>
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </Table>
    </div>
  )

  // ── 分页信息行 ───────────────────────────────────────────
  const renderPaginationRow = () => (
    <Row className="align-items-center mb-3">
      <Col md={6}>
        <div className="d-flex align-items-center">
          <span className="text-muted me-2">每页显示：</span>
          <Form.Select size="sm" style={{ width: 80 }} value={filters.per_page} onChange={handlePerPage}>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </Form.Select>
          <span className="text-muted ms-2">条</span>
          <span className="text-muted ms-3">
            共 {pagination.total} 条记录，当前第 {pagination.page}/{pagination.pages} 页
          </span>
        </div>
      </Col>
      <Col md={6}>
        {renderPagination()}
      </Col>
    </Row>
  )

  return (
    <div>
      {/* ── 轮播图 ─────────────────────────────────────── */}
      <Carousel className="mb-4" controls indicators
        style={{ borderRadius: 12, overflow: 'hidden' }}>
        {CAROUSEL_ITEMS.map((item, idx) => (
          <Carousel.Item key={idx} interval={6000}>
            <div style={{
              height: 240,
              backgroundImage: `url(${item.img})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              position: 'relative',
            }}>
              {/* 底部渐变遮罩 */}
              <div style={{
                position: 'absolute',
                bottom: 0, left: 0, right: 0,
                height: 120,
                background: 'linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 50%, transparent 100%)',
              }} />
              {/* 左下角文字 */}
              <div style={{
                position: 'absolute',
                bottom: 28, left: 28, right: 28,
                color: 'white',
                textAlign: 'left',
              }}>
                <h5 style={{ fontWeight: 'bold', marginBottom: 4, textShadow: '2px 2px 4px rgba(0,0,0,0.5)' }}>
                  <i className={`fas ${item.icon} me-2`} />{item.title}
                </h5>
                <p style={{ margin: 0, fontSize: 14, opacity: 0.95, textShadow: '1px 1px 2px rgba(0,0,0,0.5)' }}>
                  {item.desc}
                </p>
              </div>
            </div>
          </Carousel.Item>
        ))}
      </Carousel>

      {/* ── 提示消息 ────────────────────────────────────── */}
      {alertMsg && (
        <Alert variant={alertMsg.type} dismissible onClose={() => setAlertMsg(null)} className="mb-3">
          {alertMsg.msg}
        </Alert>
      )}

      {/* ── 主内容卡片 ──────────────────────────────────── */}
      <Card className="shadow-sm">
        {/* 卡片头部 */}
        <Card.Header className="bg-white d-flex justify-content-between align-items-center">
          <h5 className="mb-0">备件列表</h5>
          <div className="d-flex align-items-center gap-2 flex-wrap">
            {/* 条形码搜索 */}
            <InputGroup style={{ width: 250 }}>
              <InputGroup.Text><i className="fas fa-barcode" /></InputGroup.Text>
              <Form.Control
                ref={barcodeInputRef}
                placeholder="扫码或输入条形码搜索..."
                onKeyPress={e => {
                  if (e.key === 'Enter') {
                    handleBarcodeSearch(e.target.value)
                    e.target.value = ''
                  }
                }}
              />
            </InputGroup>

            {/* 列显示 */}
            <Dropdown show={showColDrop} onToggle={val => { setShowColDrop(val); if (val) setTempCols(visibleCols) }}>
              <Dropdown.Toggle variant="outline-secondary" id="columnSelector" title="列显示配置">
                <i className="fas fa-columns" /> 列显示
              </Dropdown.Toggle>
              <Dropdown.Menu style={{ maxHeight: 400, overflowY: 'auto', minWidth: 200 }}>
                <Dropdown.Header>选择显示的列</Dropdown.Header>
                <Dropdown.Item as="div">
                  <Form.Check
                    label="全部列"
                    checked={tempCols.length === ALL_COLUMNS.length}
                    onChange={e => setTempCols(e.target.checked ? ALL_COLUMNS.map(c => c.key) : [])}
                  />
                </Dropdown.Item>
                <Dropdown.Divider />
                {ALL_COLUMNS.map(col => (
                  <Dropdown.Item key={col.key} as="div">
                    <Form.Check
                      label={col.label}
                      checked={tempCols.includes(col.key)}
                      onChange={e => setTempCols(prev =>
                        e.target.checked ? [...prev, col.key] : prev.filter(k => k !== col.key)
                      )}
                    />
                  </Dropdown.Item>
                ))}
                <Dropdown.Divider />
                <div className="px-3 d-flex gap-2">
                  <Button size="sm" variant="primary" onClick={applyColSettings}>应用</Button>
                  <Button size="sm" variant="outline-secondary" onClick={resetColSettings}>重置</Button>
                </div>
              </Dropdown.Menu>
            </Dropdown>

            {/* 视图切换 */}
            <Button
              variant="outline-secondary"
              title={viewMode === 'table' ? '切换到卡片视图' : '切换到列表视图'}
              onClick={() => {
                const next = viewMode === 'table' ? 'card' : 'table'
                setViewMode(next)
                localStorage.setItem('sparePartsView', next)
              }}
            >
              <i className={`fas ${viewMode === 'table' ? 'fa-th' : 'fa-list'}`} />
            </Button>

            {/* 导出 */}
            <Dropdown show={showExportDrop} onToggle={setShowExportDrop}>
              <Dropdown.Toggle variant="outline-secondary" title="导出数据">
                <i className="fas fa-file-export" />
              </Dropdown.Toggle>
              <Dropdown.Menu>
                <Dropdown.Item onClick={() => handleExport('excel')}>导出 Excel</Dropdown.Item>
                <Dropdown.Item onClick={() => handleExport('csv')}>导出 CSV</Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>

            {/* 新增备件 */}
            <Button variant="primary" onClick={() => navigate('/spare_parts/new')}>
              <i className="fas fa-plus" /> 新增备件
            </Button>
          </div>
        </Card.Header>

        <Card.Body>
          {/* 搜索表单 */}
          <Row className="mb-4 g-2">
            <Col md={3}>
              <InputGroup>
                <InputGroup.Text><i className="fas fa-search" /></InputGroup.Text>
                <Form.Control
                  placeholder="搜索备件代码、名称、规格"
                  value={filters.keyword}
                  onChange={e => handleFilter('keyword', e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && handleSearch()}
                />
              </InputGroup>
            </Col>
            <Col md={2}>
              <Form.Select value={filters.category_id} onChange={e => handleFilter('category_id', e.target.value)}>
                <option value="">全部分类</option>
                {options.categories?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </Form.Select>
            </Col>
            <Col md={2}>
              <Form.Select value={filters.supplier_id} onChange={e => handleFilter('supplier_id', e.target.value)}>
                <option value="">全部供应商</option>
                {options.suppliers?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </Form.Select>
            </Col>
            <Col md={2}>
              <Form.Select value={filters.stock_status} onChange={e => handleFilter('stock_status', e.target.value)}>
                <option value="">全部状态</option>
                <option value="normal">正常</option>
                <option value="low">不足</option>
                <option value="out">缺货</option>
                <option value="overstocked">过剩</option>
              </Form.Select>
            </Col>
            <Col md={2}>
              <Form.Select value={filters.is_active} onChange={e => handleFilter('is_active', e.target.value)}>
                <option value="">全部</option>
                <option value="1">启用</option>
                <option value="0">停用</option>
              </Form.Select>
            </Col>
            <Col md={1}>
              <Button variant="primary" className="w-100" onClick={handleSearch} disabled={loading}>
                {loading ? <Spinner size="sm" animation="border" /> : <i className="fas fa-search" />}
              </Button>
            </Col>
          </Row>

          {/* 顶部分页 */}
          {pagination.pages > 1 && renderPaginationRow()}

          {/* 列表/卡片视图 */}
          {viewMode === 'table' ? renderTableView() : renderCardView()}

          {/* 底部分页 */}
          {pagination.pages > 1 && (
            <div className="mt-3">{renderPaginationRow()}</div>
          )}
        </Card.Body>
      </Card>

      {/* ── 删除确认 Modal ─────────────────────────────── */}
      <Modal show={!!deleteConfirm} onHide={() => setDeleteConfirm(null)} centered>
        <Modal.Header closeButton>
          <Modal.Title>确认删除</Modal.Title>
        </Modal.Header>
        <Modal.Body>确定要删除这个备件吗？此操作不可撤销。</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setDeleteConfirm(null)}>取消</Button>
          <Button variant="danger" onClick={() => handleDelete(deleteConfirm)}>确定删除</Button>
        </Modal.Footer>
      </Modal>

      {/* ── 图片生成进度 Modal ─────────────────────────── */}
      <Modal show={genModal.open} onHide={() => !genModal.done ? null : setGenModal(p => ({ ...p, open: false }))} centered>
        <Modal.Header closeButton={genModal.done}>
          <Modal.Title><i className="fas fa-magic me-2" />AI 图片生成</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p className="text-muted mb-2">{genModal.status}</p>
          <ProgressBar
            now={genModal.progress}
            label={`${genModal.progress}%`}
            variant={genModal.done ? 'success' : 'primary'}
            animated={!genModal.done}
            className="mb-3"
          />
          <ListGroup variant="flush">
            {genModal.items.map(item => (
              <ListGroup.Item key={item.type} className="d-flex justify-content-between align-items-center px-0">
                <span>{item.name}</span>
                {item.status === 'pending'     && <span className="text-muted"><i className="fas fa-clock" /></span>}
                {item.status === 'generating'  && <Spinner size="sm" animation="border" variant="primary" />}
                {item.status === 'success'     && <span className="text-success"><i className="fas fa-check-circle" /></span>}
                {item.status === 'error'       && <span className="text-danger"><i className="fas fa-times-circle" /></span>}
              </ListGroup.Item>
            ))}
          </ListGroup>
        </Modal.Body>
        {genModal.done && (
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setGenModal(p => ({ ...p, open: false }))}>关闭</Button>
            {genModal.items.some(i => i.status === 'error') && (
              <Button variant="primary" onClick={() => handleGenerateImages(genModal.partId)}>重试失败项</Button>
            )}
          </Modal.Footer>
        )}
      </Modal>
    </div>
  )
}
