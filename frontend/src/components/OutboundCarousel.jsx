import React, { useState } from 'react'
import { Carousel } from 'react-bootstrap'

const OutboundCarousel = () => {
  const [index, setIndex] = useState(0)

  const handleSelect = (selectedIndex) => {
    setIndex(selectedIndex)
  }

  const slides = [
    {
      src: '/static/images/carousel/outbound_01.jpg',
      title: '出库订单处理',
      subtitle: '快速响应出库需求，智能订单分配',
      icon: 'fa-shopping-cart'
    },
    {
      src: '/static/images/carousel/outbound_02.jpg',
      title: '智能拣货系统',
      subtitle: '优化拣货路径，提升作业效率',
      icon: 'fa-hand-holding-box'
    },
    {
      src: '/static/images/carousel/outbound_03.jpg',
      title: '精准配货复核',
      subtitle: '双重核对机制，确保配货准确',
      icon: 'fa-check-double'
    },
    {
      src: '/static/images/carousel/outbound_04.jpg',
      title: '自动化包装线',
      subtitle: '标准化包装流程，保护物资安全',
      icon: 'fa-box-open'
    },
    {
      src: '/static/images/carousel/outbound_05.jpg',
      title: '出库扫码核验',
      subtitle: '条码扫描出库，数据实时更新',
      icon: 'fa-barcode'
    },
    {
      src: '/static/images/carousel/outbound_06.jpg',
      title: '物流配送管理',
      subtitle: '智能调度配送，准时送达客户',
      icon: 'fa-shipping-fast'
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

export default OutboundCarousel
