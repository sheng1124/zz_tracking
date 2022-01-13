import time
import cv2 
from client_api import Video_client

if __name__ == '__main__':
    #輸入時間 ，取得那個時間的影像，預設只開60分鐘
    #s = input("輸入要看的時間點:\n")
    #連到伺服器
    vc = Video_client("163.25.103.111", 9987, "detect_request")
    vc.connect()

    source = input('enter source name\n')
    vc.set_source_name(source)

    #顯示影像
    while True:
        (t, img) = vc.get_image()
        cv2.imshow("live", img)
        cv2.waitKey(1)
        


