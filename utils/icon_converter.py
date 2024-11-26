from PIL import Image
import os

def convert_webp_to_ico():
    """webp 파일를 ICO 파일로 변환"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(project_root, "ico", "icon.webp")
    output_path = os.path.join(project_root, "ico", "folder_lock.ico")
    
    img = Image.open(input_path)
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    sizes = [(16,16), (32,32), (48,48), (256,256)]
    
    img_list = []
    for size in sizes:
        resized_img = img.resize(size, Image.Resampling.LANCZOS)
        img_list.append(resized_img)
    
    img_list[0].save(
        output_path,
        format='ICO',
        sizes=[(img.size[0], img.size[1]) for img in img_list],
        append_images=img_list[1:]
    )
    
    print(f"변환 완료: {output_path}")

if __name__ == "__main__":
    convert_webp_to_ico()