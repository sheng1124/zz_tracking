from utils.peko_utils.client import Video_povider_client

import cv2
import time

if __name__ == '__main__':
    vp = Video_povider_client("163.25.103.111", 9987)
    vp.connect()
    #"rtsp://admin:ppcb1234@192.168.154.15:554/unicast/c7/s1/live") #640 480
    cam_id = 0
    cam = cv2.VideoCapture(cam_id)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    source = input('enter source name\n')
    vp.set_source_name(source)
    while True:
        vp.send_image_from_cam(cam)


