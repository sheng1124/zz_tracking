import cv2

from client_api import Video_povider_client


if __name__ == '__main__':
    vp = Video_povider_client("163.25.103.111", 9987, "video_source")
    vp.connect()
    #"rtsp://admin:ppcb1234@192.168.154.15:554/unicast/c7/s1/live") #640 480
    cam = cv2.VideoCapture(0)

    while True:
        vp.send_image_from_cam(cam)

