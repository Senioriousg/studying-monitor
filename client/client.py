from PIL import ImageGrab
import requests
import time
import io
import os

SERVER_URL = "http://localhost:9160/upload"  # 替换为实际地址
USER_ID = "user01"  # 每个客户端需要不同ID

def capture_and_upload():
    while True:
        try:
            # 截屏并压缩
            img = ImageGrab.grab()
            img = img.resize((630, 390)).convert("RGB")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=20)
            
            # 上传
            files = {'image': ('screen.jpg', img_bytes.getvalue())}
            data = {'user_id': USER_ID}
            requests.post(SERVER_URL, files=files, data=data)
            
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(3)  # 1秒间隔

if __name__ == '__main__':
    capture_and_upload()
