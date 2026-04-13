import React, { useState } from 'react'
import { Carousel } from 'react-bootstrap'

const InventoryCarousel = () => {
  const [index, setIndex] = useState(0)

  const handleSelect = (selectedIndex) => {
    setIndex(selectedIndex)
  }

  const slides = [
    {
      src: '/static/images/carousel/inventory_01.jpg',
      title: '实时库存监控',
      subtitle: '24 小时库存动态追踪，数据实时可视',
      icon: 'fa-chart-line'
    },
    {
      src: '/static/images/carousel/inventory_02.jpg',
      title: '智能库存预警',
      subtitle: '自动监测库存水位，及时补货提醒',
      icon: 'fa-bell'
    },
    {
      src: '/static/images/carousel/inventory_03.jpg',
      title: '定期库存盘点',
      subtitle: '周期性盘点核对，确保账实相符',
      icon: 'fa-clipboard-list'
    },
    {
      src: '/static/images/carousel/inventory_04.jpg',
      title: '货位优化管理',
      subtitle: '科学货位规划，提升空间利用率',
      icon: 'fa-map-marked-alt'
    },
    {
      src: '/static/images/carousel/inventory_05.jpg',
      title: '批次追溯管理',
      subtitle: '完整批次记录，全生命周期可追溯',
      icon: 'fa-history'
    },
    {
      src: '/static/images/carousel/inventory_06.jpg',
      title: '库存调拨管理',
      subtitle: '灵活库存调配，优化资源配置',
      icon: 'fa-exchange-alt'
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

export default InventoryCarousel
