import os
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import exifread

def get_exif_datetime(image_path):
    """从图片中读取EXIF信息中的拍摄时间"""
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
            
            # 尝试不同的EXIF标签获取拍摄时间
            datetime_tags = ['EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Image DateTime']
            for tag in datetime_tags:
                if tag in tags:
                    # 将EXIF时间格式（YYYY:MM:DD HH:MM:SS）转换为Python datetime对象
                    date_str = str(tags[tag])
                    try:
                        return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        continue
            
            # 如果没有找到EXIF时间，使用文件的修改时间
            file_mtime = os.path.getmtime(image_path)
            return datetime.fromtimestamp(file_mtime)
    except Exception as e:
        print(f"无法读取{image_path}的EXIF信息: {e}")
        # 发生错误时返回当前时间
        return datetime.now()

def add_watermark(image_path, output_path, text, font_size=20, font_color=(255, 255, 255), position='bottom_right', opacity=128):
    """在图片上添加水印"""
    try:
        # 打开图片
        image = Image.open(image_path).convert('RGBA')
        
        # 创建一个与原图大小相同的透明图层
        watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            # 在Windows上使用完整的Arial字体路径
            if os.name == 'nt':  # Windows系统
                font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', font_size)
            else:
                # 非Windows系统尝试其他字体
                font = ImageFont.truetype('arial.ttf', font_size)
        except IOError:
            # 在不同平台上尝试其他常见字体
            try:
                font = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', font_size)  # macOS
            except IOError:
                try:
                    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)  # Linux
                except IOError:
                    # 如果都失败，使用默认字体
                    font = ImageFont.load_default()
                    print("警告: 无法加载指定字体，使用默认字体")
        
        # 获取文本大小 - 兼容新版Pillow
        # 注意：Pillow 8.0.0+中textsize方法已废弃，改用getbbox方法
        try:
            # 尝试使用font.getbbox (Pillow 8.0.0+)
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # 对于旧版Pillow使用draw.textsize
            text_width, text_height = draw.textsize(text, font=font)
        
        # 根据位置确定文本的放置位置
        if position == 'top_left':
            x, y = 10, 10
        elif position == 'top_right':
            x, y = image.width - text_width - 10, 10
        elif position == 'bottom_left':
            x, y = 10, image.height - text_height - 10
        elif position == 'center':
            x, y = (image.width - text_width) // 2, (image.height - text_height) // 2
        else:  # bottom_right
            x, y = image.width - text_width - 10, image.height - text_height - 10
        
        # 在透明图层上绘制文本
        draw.text((x, y), text, font=font, fill=font_color + (opacity,))
        
        # 将透明图层与原图合并
        combined = Image.alpha_composite(image, watermark_layer)
        
        # 保存结果图片
        combined.convert('RGB').save(output_path)
        print(f"已保存带水印的图片到: {output_path}")
        return True
    except Exception as e:
        print(f"处理{image_path}时出错: {e}")
        return False

def main():
    print("===== 图片水印工具 =====")
    
    # 使用input获取用户输入
    image_path = input("请输入图片文件或目录路径: ").strip()
    
    # 默认值
    default_font_size = 20
    default_font_color = 'white'
    default_position = 'bottom_right'
    default_opacity = 128
    
    # 获取可选参数，用户直接按回车则使用默认值
    font_size_input = input(f"请输入水印字体大小 (默认: {default_font_size}): ").strip()
    font_size = int(font_size_input) if font_size_input else default_font_size
    
    font_color_input = input(f"请输入水印字体颜色 (默认: {default_font_color}, 支持英文名称或RGB格式如255,255,255): ").strip()
    font_color_str = font_color_input if font_color_input else default_font_color
    
    position_input = input(f"请输入水印位置 (默认: {default_position}, 可选值: top_left, top_right, bottom_left, bottom_right, center): ").strip()
    position = position_input if position_input else default_position
    
    opacity_input = input(f"请输入水印透明度 (默认: {default_opacity}, 范围: 0-255): ").strip()
    opacity = int(opacity_input) if opacity_input else default_opacity
    
    # 验证位置参数
    valid_positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right', 'center']
    if position not in valid_positions:
        print(f"警告: 无效的位置值 '{position}'，使用默认值 'bottom_right'")
        position = default_position
    
    # 验证透明度参数
    if not (0 <= opacity <= 255):
        print(f"警告: 透明度值 {opacity} 超出范围，使用默认值 {default_opacity}")
        opacity = default_opacity
    
    # 处理字体颜色参数
    if font_color_str.lower() == 'white':
        font_color = (255, 255, 255)
    elif font_color_str.lower() == 'black':
        font_color = (0, 0, 0)
    elif font_color_str.lower() == 'red':
        font_color = (255, 0, 0)
    elif font_color_str.lower() == 'green':
        font_color = (0, 255, 0)
    elif font_color_str.lower() == 'blue':
        font_color = (0, 0, 255)
    else:
        # 尝试解析RGB格式
        try:
            font_color = tuple(map(int, font_color_str.split(',')))
            if len(font_color) != 3 or not all(0 <= c <= 255 for c in font_color):
                raise ValueError
        except ValueError:
            print(f"无效的颜色格式: {font_color_str}，使用默认白色")
            font_color = (255, 255, 255)
    
    # 检查输入路径
    if not os.path.exists(image_path):
        print(f"错误: 路径 {image_path} 不存在")
        return
    
    # 确定是文件还是目录
    if os.path.isfile(image_path):
        # 单个文件处理
        process_single_file(image_path, font_size, font_color, position, opacity)
    else:
        # 目录处理
        process_directory(image_path, font_size, font_color, position, opacity)

def process_single_file(file_path, font_size, font_color, position, opacity):
    """处理单个图片文件"""
    # 检查文件是否为图片
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
    _, ext = os.path.splitext(file_path.lower())
    if ext not in image_extensions:
        print(f"跳过非图片文件: {file_path}")
        return
    
    # 获取图片的目录和文件名
    dir_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    
    # 创建输出目录
    output_dir = os.path.join(dir_path, f"{os.path.basename(dir_path)}_watermark")
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取水印文本
    datetime_obj = get_exif_datetime(file_path)
    watermark_text = datetime_obj.strftime('%Y-%m-%d')
    
    # 构建输出文件路径
    output_path = os.path.join(output_dir, file_name)
    
    # 添加水印并保存
    add_watermark(file_path, output_path, watermark_text, font_size, font_color, position, opacity)

def process_directory(dir_path, font_size, font_color, position, opacity):
    """处理目录中的所有图片文件"""
    # 创建输出目录
    output_dir = os.path.join(dir_path, f"{os.path.basename(dir_path)}_watermark")
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍历目录中的所有文件
    for file_name in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file_name)
        
        # 跳过子目录
        if os.path.isdir(file_path):
            continue
        
        # 检查文件是否为图片
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
        _, ext = os.path.splitext(file_name.lower())
        if ext not in image_extensions:
            print(f"跳过非图片文件: {file_name}")
            continue
        
        # 获取水印文本
        datetime_obj = get_exif_datetime(file_path)
        watermark_text = datetime_obj.strftime('%Y-%m-%d')
        
        # 构建输出文件路径
        output_path = os.path.join(output_dir, file_name)
        
        # 添加水印并保存
        add_watermark(file_path, output_path, watermark_text, font_size, font_color, position, opacity)

if __name__ == "__main__":
    main()