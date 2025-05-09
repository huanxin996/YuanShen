import base64
from io import BytesIO
from PIL import Image


class ImageManager:

    def image_to_base64(self, img: Image.Image, format='PNG') -> str:
        output_buffer = BytesIO()
        img.save(output_buffer, format)
        byte_data = output_buffer.getvalue()
        base64_str = base64.b64encode(byte_data).decode()
        return 'base64://' + base64_str


image_manager = ImageManager()