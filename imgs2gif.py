import os
import time

import imageio
from PIL import Image,ImageSequence

from pic_input import get_pic_floder_list, get_pictures

if __name__ == '__main__2':
    #取得資料夾列表
    pic_floder_list = get_pic_floder_list()

    #整理資料夾下所有圖片路徑
    pictures = get_pictures(pic_floder_list)

    #製作 gif
    images = []
    stime, etime, imlen = (0,0,0)
    for filepath, ftime in pictures:#545-616.jpg
        if stime == 0:
            stime = ftime
        
        try:
            p = int(filepath[-7:-4])
            if 545 <= p <= 616:
                images.append(imageio.imread(filepath))
        except:
            pass
        #images.append(imageio.imread(filepath))
        etime = ftime
        imlen += 1
    
    #計算影像間隔秒數
    #du = (etime - stime) / imlen
    du = 1/12
    
    #儲存gif檔
    y, m, d, h, mm, *_ = time.localtime()
    now_time = "{}-{}-{}T{}-{}.gif".format(y, m, d, h, mm)
    imageio.mimsave(os.path.join('data/gif/', now_time), images, 'GIF', duration=du)


if __name__ == '__main__':
    #取得資料夾列表
    pic_floder_list = get_pic_floder_list()

    #整理資料夾下所有圖片路徑
    pictures = get_pictures(pic_floder_list)

    #製作 gif
    images = []
    stime, etime, imlen = (0,0,0)
    for filepath, ftime in pictures:#545-616.jpg
        if stime == 0:
            stime = ftime
        
        try:
            p = int(filepath[-7:-4])
            if 545 <= p <= 614:
                images.append(Image.open(filepath))
        except:
            pass
        #images.append(imageio.imread(filepath))
        etime = ftime
        imlen += 1
    
    #計算影像間隔秒數
    #du = (etime - stime) / imlen
    du = 1/12
    
    #儲存gif檔
    y, m, d, h, mm, *_ = time.localtime()
    now_time = "{}-{}-{}T{}-{}.gif".format(y, m, d, h, mm)
    images[0].save(os.path.join('data/gif/', now_time), quality=100,save_all=True, append_images=images[1:], duration=1000/12, loop=0, disposal=0)

