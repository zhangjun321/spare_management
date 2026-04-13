import React, { useState } from 'react'
import { Carousel } from 'react-bootstrap'

const InboundCarousel = () => {
  const [index, setIndex] = useState(0)

  const handleSelect = (selectedIndex) => {
    setIndex(selectedIndex)
  }

  const slides = [
    {
      src: '/static/images/carousel/inbound_01.jpg',
      title: '物资到货接收',
      subtitle: '快速响应供应商送货，高效卸货验收',
      icon: 'fa-truck-loading'
    },
    {
      src: '/static/images/carousel/inbound_02.jpg',
      title: '严格质量检验',
      subtitle: '专业质检流程，确保入库物资品质',
      icon: 'fa-clipboard-check'
    },
    {
      src: '/static/images/carousel/inbound_03.jpg',
      title: '智能条码扫描',
      subtitle: '自动化数据采集，精准录入系统',
      icon: 'fa-barcode'
    },
    {
      src: '/static/images/carousel/inbound_04.jpg',
      title: '规范上架流程',
      subtitle: '科学货位分配，整齐有序存储',
      icon: 'fa-dolly'
    },
    {
      src: '/static/images/carousel/inbound_05.jpg',
      title: '入库单据管理',
      subtitle: '电子化单据流转，可追溯可查询',
      icon: 'fa-file-invoice'
    },
    {
      src: '/static/images/carousel/inbound_06.jpg',
      title: '自动化分拣系统',
      subtitle: '智能输送线，高效分拣入库',
      icon: 'fa-conveyor-belt'
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

export default InboundCarousel
