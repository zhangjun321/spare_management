import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import os
from flask import current_app
from PIL import Image


def generate_barcode(barcode_data, barcode_type='code128', write_text=True, 
                    quiet_zone=6.5, module_width=0.2, module_height=15.0):
    """
    生成条形码图片
    
    Args:
        barcode_data: 条形码数据
        barcode_type: 条形码类型，默认为 code128
        write_text: 是否显示文本，默认为 True
        quiet_zone: 安静区域大小，默认为 6.5
        module_width: 模块宽度，默认为 0.2
        module_height: 模块高度，默认为 15.0
    
    Returns:
        条形码图片的二进制数据
    """
    try:
        # 获取条形码类
        CodeClass = barcode.get_barcode_class(barcode_type)
        
        # 创建条形码对象
        code = CodeClass(barcode_data, writer=ImageWriter())
        
        # 生成条形码
        buffer = BytesIO()
        code.write(buffer, options={
            'write_text': write_text,
            'quiet_zone': quiet_zone,
            'module_width': module_width,
            'module_height': module_height
        })
        
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        current_app.logger.error(f'生成条形码失败: {str(e)}')
        return None


def save_barcode_to_file(barcode_data, file_path, barcode_type='code128', **kwargs):
    """
    生成条形码并保存到文件
    
    Args:
        barcode_data: 条形码数据
        file_path: 保存文件路径
        barcode_type: 条形码类型，默认为 code128
        **kwargs: 其他条形码生成参数
    
    Returns:
        成功返回 True，失败返回 False
    """
    barcode_bytes = generate_barcode(barcode_data, barcode_type, **kwargs)
    if barcode_bytes:
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(barcode_bytes)
            return True
        except Exception as e:
            current_app.logger.error(f'保存条形码文件失败: {str(e)}')
            return False
    return False


def generate_barcode_for_spare_part(spare_part, use_part_code=True):
    """
    为备件生成条形码
    
    Args:
        spare_part: 备件对象
        use_part_code: 是否使用备件代码作为条形码数据，默认为 True
    
    Returns:
        (条形码数据, 条形码图片二进制数据)
    """
    if use_part_code and spare_part.part_code:
        barcode_data = spare_part.part_code
    elif spare_part.barcode:
        barcode_data = spare_part.barcode
    else:
        # 如果没有备件代码和条形码，使用ID生成
        barcode_data = f'SP{spare_part.id:06d}'
    
    barcode_bytes = generate_barcode(barcode_data)
    return barcode_data, barcode_bytes


def get_barcode_image_url(spare_part):
    """
    获取备件条形码图片的URL路径
    
    Args:
        spare_part: 备件对象
    
    Returns:
        条形码图片的URL路径，如果不存在返回 None
    """
    if not spare_part.barcode:
        return None
    
    # 构建条形码文件路径
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    barcode_folder = os.path.join(upload_folder, 'barcodes')
    filename = f'{spare_part.part_code or spare_part.id}.png'
    file_path = os.path.join(barcode_folder, filename)
    
    # 如果文件不存在，生成它
    if not os.path.exists(file_path):
        barcode_data, barcode_bytes = generate_barcode_for_spare_part(spare_part)
        if barcode_bytes:
            save_barcode_to_file(barcode_data, file_path)
    
    if os.path.exists(file_path):
        return f'/uploads/barcodes/{filename}'
    
    return None
