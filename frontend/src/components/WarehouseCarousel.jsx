import React, { useState, useEffect } from 'react'
import { Carousel } from 'react-bootstrap'

const WarehouseCarousel = () => {
  const [index, setIndex] = useState(0)

  const handleSelect = (selectedIndex) => {
    setIndex(selectedIndex)
  }

  const slides = [
    {
      src: '/static/images/carousel/warehouse_01.jpg',
      title: '智能化立体仓库',
      subtitle: '现代化仓储设施，智能化管理系统',
      icon: 'fa-warehouse'
    },
    {
      src: '/static/images/carousel/warehouse_02.jpg',
      title: '规范入库流程',
      subtitle: '严格质检入库，确保物资品质',
      icon: 'fa-download'
    },
    {
      src: '/static/images/carousel/warehouse_03.jpg',
      title: '高效出库管理',
      subtitle: '快速响应需求，精准配货出库',
      icon: 'fa-upload'
    },
    {
      src: '/static/images/carousel/warehouse_04.jpg',
      title: '实时库存监控',
      subtitle: '精准库存预警，智能补货建议',
      icon: 'fa-boxes'
    },
    {
      src: '/static/images/carousel/warehouse_05.jpg',
      title: 'AI 智能分析',
      subtitle: '数据驱动决策，优化库存周转',
      icon: 'fa-brain'
    },
    {
      src: '/static/images/carousel/warehouse_06.jpg',
      title: '智能货位管理',
      subtitle: '科学货位规划，提升空间利用率',
      icon: 'fa-map-marker-alt'
    }
  ]

  return (
    <Carousel 
      activeIndex={index} 
      onSelect={handleSelect} 
      className="mb-4"
      style={{ borderRadius: '12px', overflow: 'hidden' }}
      controls={true}
      indicators={true}
    >
      {slides.map((slide, idx) => (
        <Carousel.Item key={idx} interval={6000}>
          <div 
            style={{
              height: '600px',
              backgroundImage: `url(${slide.src})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              position: 'relative'
            }}
          >
            {/* 渐变遮罩 - 底部渐变效果 */}
            <div 
              style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                height: '150px',
                background: 'linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 50%, transparent 100%)'
              }}
            />
            
            {/* 文字描述 - 与备件管理系统一致的风格 */}
            <div 
              style={{
                position: 'absolute',
                bottom: '30px',
                left: '30px',
                right: '30px',
                color: 'white',
                textAlign: 'left'
              }}
            >
              <h3 style={{ 
                fontSize: '28px', 
                fontWeight: 'bold',
                marginBottom: '8px',
                textShadow: '2px 2px 4px rgba(0,0,0,0.5)'
              }}>
                <i className={`fas ${slide.icon} me-2`}></i>
                {slide.title}
              </h3>
              <p style={{ 
                fontSize: '16px', 
                margin: 0,
                opacity: 0.95,
                textShadow: '1px 1px 2px rgba(0,0,0,0.5)'
              }}>
                {slide.subtitle}
              </p>
            </div>
          </div>
        </Carousel.Item>
      ))}
    </Carousel>
  )
}

export default WarehouseCarousel
