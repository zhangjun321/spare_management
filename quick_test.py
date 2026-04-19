#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试脚本
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
app = create_app()

with app.app_context():
    print("App created successfully!\n")
    
    print("Testing KPI module...")
    from app.services.kpi_service import get_kpi_service
    kpi_service = get_kpi_service()
    kpi_service.init_default_kpis()
    
    from app.models.kpi import KPIConfig
    kpis = KPIConfig.query.all()
    print(f"  KPI configs: {len(kpis)}")
    for kpi in kpis:
        print(f"  - {kpi.name} ({kpi.code})")
    
    print("\nTesting AI module...")
    from app.services.dashboard_ai_service import get_dashboard_ai_service
    ai_service = get_dashboard_ai_service()
    
    health_result = ai_service.get_inventory_health_score()
    print(f"  Health score: {health_result['health_score']}")
    print(f"  Summary: {health_result['summary']}")
    
    print("\nTesting KPI summary...")
    summary = kpi_service.get_kpi_summary()
    print(f"  KPI summary has {len(summary)} metrics:")
    for kpi in summary:
        print(f"  - {kpi['name']}: {kpi['actual_value']} {kpi['unit']}")
    
    print("\nAll features tested successfully!")
    print("\nProject is ready! You can visit: http://127.0.0.1:5000")
