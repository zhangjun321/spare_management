from app import create_app, db
from app.models.spare_part import SparePart

app = create_app()

with app.app_context():
    # 查找备件
    part = SparePart.query.filter_by(name='SKF 6204-2RS1 深沟球轴承').first()
    
    if not part:
        part = SparePart.query.filter_by(part_code='SKF-A-001').first()
    
    if part:
        print(f"找到备件：{part.part_code} - {part.name}")
        print(f"ID: {part.id}")
        print(f"\n图片 URL:")
        print(f"  image_url: '{part.image_url}'")
        print(f"  thumbnail_url: '{part.thumbnail_url}'")
        print(f"  side_image_url: '{part.side_image_url}'")
        print(f"  detail_image_url: '{part.detail_image_url}'")
        print(f"  circuit_image_url: '{part.circuit_image_url}'")
        print(f"  perspective_image_url: '{part.perspective_image_url}'")
    else:
        print("未找到备件")
