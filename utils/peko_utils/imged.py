import struct
import cv2
import numpy as np

#修改圖片
class ImageEd():
    def __init__(self):
        #解/編碼參數設定
        self.encode_parm=[int(cv2.IMWRITE_JPEG_QUALITY), 100]
        #struct 參數設定
        self.payload = ">Ld"
        self.payload_size = struct.calcsize(self.payload)

    #影像壓縮
    def compress(self, img) -> bytes:
        #影像壓縮
        ret, img_encode = cv2.imencode(".jpg", img, self.encode_parm)
        img_encode_byte = img_encode.tobytes()
        return img_encode_byte
    
    #影像打包成 socket 中的傳輸格式 需要影像的資訊 拍照時間
    def pack(self, img, gtime) -> bytearray:
        #影像壓縮
        img_encode_byte = self.compress(img)
        
        #取得影像長度
        img_encode_byte_size = len(img_encode_byte)

        #打包影像資訊 影像長度 影像時間
        packed = bytearray(struct.pack(self.payload, img_encode_byte_size, gtime))
        packed += img_encode_byte

        return packed
    
    #影像從socket解包
    def unpack(self, conn):
        buffer = bytearray()
        #從連線取得小部分資料
        buffer += conn.recv(4096)
        if not buffer:
            raise ConnectionError("no data from connection")
        #影像長度、時間資訊是 recv 過來的資料 位置 [0 ~ payload_size] 區段的位元組
        encode_img_size = buffer[:self.payload_size]
        #解碼影像資訊
        img_size, gtime = struct.unpack(self.payload, encode_img_size)
        #清空在 buffer 中的影像資訊 方便後續處理資料
        buffer = buffer[self.payload_size:]
        #直接要影像長度的資料
        while len(buffer) < img_size:
            data = conn.recv(img_size - len(buffer))
            if not data:
                raise ConnectionError("no data from connection")
            buffer += data
        #擷取、解析壓縮影像資訊
        encode_img = buffer[:img_size]
        #影像解碼
        img = cv2.imdecode(np.frombuffer(encode_img, dtype = "uint8"), cv2.IMREAD_COLOR)

        return img, gtime

    