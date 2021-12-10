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
    client.recv(1)
    while True:
        #in_data =  client.recv(1024)
        #print("From Server :" ,in_data.decode())
        out_data = input()
        client.sendall(bytes(out_data,'UTF-8'))
        if out_data=='bye':
            break
    client.close()
    

if __name__ == '__main__':
    main3()