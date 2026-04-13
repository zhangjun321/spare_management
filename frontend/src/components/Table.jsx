import React, { useState, useMemo } from 'react'
import { Table, Pagination, Form, InputGroup, Button } from 'react-bootstrap'
import { FaSearch, FaSort, FaSortUp, FaSortDown } from 'react-icons/fa'

const DataTable = ({
  columns = [],
  data = [],
  searchable = false,
  sortable = true,
  pagination = true,
  pageSize = 10,
  onRowClick,
  actions,
  className,
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })

  // 搜索过滤
  const filteredData = useMemo(() => {
    if (!searchTerm) return data
    
    return data.filter((item) =>
      columns.some((column) => {
        const value = item[column.key]
        return value && String(value).toLowerCase().includes(searchTerm.toLowerCase())
      })
    )
  }, [data, searchTerm, columns])

  // 排序
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return filteredData

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortConfig.key]
      const bValue = b[sortConfig.key]

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })
  }, [filteredData, sortConfig])

  // 分页
  const paginatedData = useMemo(() => {
    if (!pagination) return sortedData
    
    const startIndex = (currentPage - 1) * pageSize
    const endIndex = startIndex + pageSize
    return sortedData.slice(startIndex, endIndex)
  }, [sortedData, currentPage, pageSize, pagination])

  const totalPages = Math.ceil(filteredData.length / pageSize)

  // 处理排序
  const handleSort = (key) => {
    if (!sortable) return

    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }))
  }

  // 重置分页
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value)
    setCurrentPage(1)
  }

  // 渲染排序图标
  const renderSortIcon = (column) => {
    if (!sortable || !column.sortable) return null

    if (sortConfig.key !== column.key) {
      return <FaSort className="text-muted ml-1" size={12} />
    }

    return sortConfig.direction === 'asc' ? (
      <FaSortUp className="ml-1" size={12} />
    ) : (
      <FaSortDown className="ml-1" size={12} />
    )
  }

  // 渲染表头
  const renderHeader = () => (
    <thead>
      <tr>
        {columns.map((column) => (
          <th
            key={column.key}
            onClick={() => handleSort(column.key)}
            style={{
              cursor: sortable && column.sortable !== false ? 'pointer' : 'default',
              whiteSpace: 'nowrap',
              ...column.headerStyle,
            }}
            className={column.headerClassName}
          >
            <div className="d-flex align-items-center">
              {column.title}
              {renderSortIcon(column)}
            </div>
          </th>
        ))}
        {actions && <th style={{ width: '150px' }}>操作</th>}
      </tr>
    </thead>
  )

  // 渲染行
  const renderRows = () =>
    paginatedData.map((item, index) => (
      <tr
        key={item.id || index}
        onClick={() => onRowClick && onRowClick(item)}
        style={{
          cursor: onRowClick ? 'pointer' : 'default',
          ...column?.rowStyle,
        }}
        className={column?.rowClassName}
      >
        {columns.map((column) => (
          <td key={column.key} style={column.cellStyle} className={column.cellClassName}>
            {column.render ? column.render(item[column.key], item, index) : item[column.key]}
          </td>
        ))}
        {actions && (
          <td>
            <div className="d-flex gap-2">{actions(item)}</div>
          </td>
        )}
      </tr>
    ))

  // 渲染分页
  const renderPagination = () => {
    if (!pagination || totalPages <= 1) return null

    const pageNumbers = []
    const maxVisible = 5
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2))
    let endPage = Math.min(totalPages, startPage + maxVisible - 1)

    if (endPage - startPage < maxVisible - 1) {
      startPage = Math.max(1, endPage - maxVisible + 1)
    }

    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i)
    }

    return (
      <div className="d-flex justify-content-between align-items-center mt-3">
        <div className="text-muted">
          显示 {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, filteredData.length)} 条，
          共 {filteredData.length} 条
        </div>
        <Pagination className="mb-0">
          <Pagination.First onClick={() => setCurrentPage(1)} disabled={currentPage === 1} />
          <Pagination.Prev
            onClick={() => setCurrentPage(currentPage - 1)}
            disabled={currentPage === 1}
          />
          {pageNumbers.map((number) => (
            <Pagination.Item
              key={number}
              active={number === currentPage}
              onClick={() => setCurrentPage(number)}
            >
              {number}
            </Pagination.Item>
          ))}
          <Pagination.Next
            onClick={() => setCurrentPage(currentPage + 1)}
            disabled={currentPage === totalPages}
          />
          <Pagination.Last
            onClick={() => setCurrentPage(totalPages)}
            disabled={currentPage === totalPages}
          />
        </Pagination>
      </div>
    )
  }

  return (
    <div className={className}>
      {/* 搜索框 */}
      {searchable && (
        <div className="mb-3">
          <InputGroup>
            <InputGroup.Text>
              <FaSearch />
            </InputGroup.Text>
            <Form.Control
              placeholder="搜索..."
              value={searchTerm}
              onChange={handleSearchChange}
              style={{ maxWidth: '300px' }}
            />
          </InputGroup>
        </div>
      )}

      {/* 表格 */}
      <div className="table-responsive">
        <Table hover striped bordered className="align-middle">
          {renderHeader()}
          <tbody>{renderRows()}</tbody>
        </Table>
      </div>

      {/* 分页 */}
      {renderPagination()}
    </div>
  )
}

export default DataTable
