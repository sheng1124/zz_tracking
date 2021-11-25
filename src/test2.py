import socket
import struct
import cv2
import numpy as np

def main3():
    SERVER = "163.25.103.111"
    PORT = 9987
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    client.sendall(bytes("msg_source",'UTF-8'))
    while True:
        #in_data =  client.recv(1024)
        #print("From Server :" ,in_data.decode())
        out_data = input()
        client.sendall(bytes(out_data,'UTF-8'))
        if out_data=='bye':
            break
    client.close()
    

def main():
    SERVER = "163.25.103.111"
    PORT = 9987
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    client.sendall(bytes("msg_request",'UTF-8'))
    while True:
        in_data =  client.recv(1024)
        print("From Server :" ,in_data.decode())
        #out_data = input()
        #client.sendall(bytes(out_data,'UTF-8'))
        if in_data=='bye':
            break
    client.close()

def main7():
    SERVER = "163.25.103.111"
    PORT = 9987
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    client.sendall(bytes("video_request",'UTF-8'))

    payload = ">L"
    payload_size = struct.calcsize(payload)
    buffer = b""

    while True:
        while len(buffer) < payload_size:
            buffer += client.recv(4096)
        packed_img_size = buffer[:payload_size]
        img_size = struct.unpack(payload, packed_img_size)[0]
        print(img_size)
        buffer = buffer[payload_size:]

        while len(buffer) < img_size:
            buffer += client.recv(img_size - len(buffer))
        packed_image = buffer[:img_size]
        buffer = buffer[img_size:]

        data = np.frombuffer(packed_image, dtype = "uint8")
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        try:
            cv2.imshow("live", image)
            cv2.waitKey(1)
        
        except Exception as e:
            print(e)

        

    client.close()

if __name__ == '__main__':
    main7()