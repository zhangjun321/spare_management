from app import create_app
from app.extensions import db
from app.models.spare_part import SparePart

app = create_app()
app.app_context().push()

part = SparePart.query.filter_by(part_code='SKF-A-001').first()
if part:
    print(f'ID: {part.id}')
    print(f'Part Code: {part.part_code}')
    print(f'image_url: "{part.image_url}"')
    print(f'thumbnail_url: "{part.thumbnail_url}"')
    print(f'side_image_url: "{part.side_image_url}"')
    print(f'detail_image_url: "{part.detail_image_url}"')
    print(f'circuit_image_url: "{part.circuit_image_url}"')
    print(f'perspective_image_url: "{part.perspective_image_url}"')
else:
    print('备件不存在')
