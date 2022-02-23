import time
import os

from client_api import Video_povider_client

#取得資料夾列表
def get_pic_floder_list():
    pic_floder_list = []
    pic_floder = input('輸入資料夾路徑 輸入q 離開\n')
    while pic_floder != 'q':
        pic_floder_list.append(pic_floder)
        pic_floder = input('輸入資料夾路徑 輸入q 離開\n')
    return pic_floder_list

#生成圖片路徑和時間
def get_pictures(pic_floder_list):
    for pic_floder in pic_floder_list:
        if not os.path.isdir(pic_floder):
            continue
        #取的資料夾下所有檔案
        fp_list = os.listdir(pic_floder)
        #整理文件排序
        fp_list = sorted(fp_list, key = lambda id:float(id[:-4]))
        for filename in fp_list:
            #解析所有圖檔路徑並解析時間
            if filename[-4:] in ('.jpg', '.png'):
                filepath = os.path.join(pic_floder, filename)
                ftime = float(filename[:-4])
                yield (filepath, ftime)

if __name__ == '__main__':
    vp = Video_povider_client("163.25.103.111", 9987, "video_source")
    vp.connect()
    #"rtsp://admin:ppcb1234@192.168.154.15:554/unicast/c7/s1/live") #640 480

    #取得資料夾列表
    pic_floder_list = get_pic_floder_list()
 
    #設定影像來源名稱
    source = input('輸入來源名稱\n')
    vp.set_source_name(source)

    pictures = get_pictures(pic_floder_list)
    print('ready to send time = ', time.asctime(time.localtime()))
    vp.response()
    while True:
        if vp.is_transport():
            #伺服器允許傳送
            try:
                filepath, ftime = next(pictures)
                vp.send_image_by_path(filepath, ftime)
            except StopIteration:
                endtime = time.time()
                print('end to send, time = ', time.asctime(time.localtime(endtime)))
                vp.response()
                vp.close()
                break
            
        else:
            vp.response()


