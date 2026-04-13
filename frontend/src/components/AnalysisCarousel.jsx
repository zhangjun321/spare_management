import React, { useState } from 'react'
import { Carousel } from 'react-bootstrap'

const AnalysisCarousel = () => {
  const [index, setIndex] = useState(0)

  const handleSelect = (selectedIndex) => {
    setIndex(selectedIndex)
  }

  const slides = [
    {
      src: '/static/images/carousel/analysis_01.jpg',
      title: 'AI 智能分析',
      subtitle: '人工智能驱动，深度数据挖掘分析',
      icon: 'fa-brain'
    },
    {
      src: '/static/images/carousel/analysis_02.jpg',
      title: '库存周转分析',
      subtitle: '优化库存结构，提升资金周转效率',
      icon: 'fa-sync-alt'
    },
    {
      src: '/static/images/carousel/analysis_03.jpg',
      title: '需求预测模型',
      subtitle: '大数据预测算法，精准需求预判',
      icon: 'fa-chart-predictive'
    },
    {
      src: '/static/images/carousel/analysis_04.jpg',
      title: '成本效益分析',
      subtitle: '精细化成本核算，提升运营效益',
      icon: 'fa-coins'
    },
    {
      src: '/static/images/carousel/analysis_05.jpg',
      title: '数据可视化',
      subtitle: '多维度数据展示，一目了然',
      icon: 'fa-chart-bar'
    },
    {
      src: '/static/images/carousel/analysis_06.jpg',
      title: '智能决策支持',
      subtitle: '数据驱动决策，科学管理依据',
      icon: 'fa-lightbulb'
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

export default AnalysisCarousel
