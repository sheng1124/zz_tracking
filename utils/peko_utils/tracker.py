#管理追蹤者 管理並指派框給追蹤者
#一個box至少指派一個tracker
#一個tracker只能指派一個box

import math


class Tracker_manager():
    def __init__(self) -> None:
        self.tracker_list=[]
        self.untrack_list = []
        self.used_id = 0
        #向資料庫取的場域資訊
        #檢查點設定
        check_area_list = [[30, 412, 133, 477], [545, 422, 636, 477]]
        self.set_check_area(check_area_list)

        #設定檢查點之間的實際距離[ [0 1], [1 0] ]
        distance_matrix_list = [0, 2.238, 565.107, 0]
        self.set_distance_matrix(distance_matrix_list)
    
    #設定檢查點區域
    def set_check_area(self, check_area_list):
        self.check_area_list = [] #[ 0:[0, 0, 10, 10] , 1:[20, 20, 30, 30] ]
        for e in check_area_list:
            self.check_area_list.append(e)

    #設定檢查點之間的距離
    def set_distance_matrix(self, distance_list): # 0 1 1 0, cl = 2
        self.distance_matrix = []
        i = 0
        a = []
        for e in distance_list:
            if i == len(self.check_area_list):
                i = 0
                self.distance_matrix.append(a)
                a = []
            a.append(e)
            i += 1
        self.distance_matrix.append(a)

    def input_boxs(self, results, gtime, shape):
        #收到新的辨識結果 重置追蹤列表 變為未追蹤狀態
        self.untrack_list, self.tracker_list = self.tracker_list, self.untrack_list
        #評估每一個box 並指派給tracker 同時把追蹤過的tracker放進已追蹤列表
        h, w = int(shape[0]), int(shape[1])
        for box in results: 
            #ex: (x1, y1, x2, y2) = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
            #print('evaluate', box, 'time', gtime)
            [x1, y1, x2, y2] = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
            self.eval_campare([x1, y1, x2, y2], gtime)
        #有重疊的情況(一個box有兩個適合的tracker) 需要多重比較
        #還沒指派的box(有重疊)會先放到eval_table ?
        #檢查未追蹤列表 這裡應該所有的box會指派完 若有剩餘的 檢查是否離場或躲起來
        for i in range(len(self.untrack_list)):
            tracker = self.untrack_list.pop()
            #tracker 計算目前與上一個box的時間差
            td = tracker.count_time_diff(gtime)
            if td <= 3:
                self.tracker_list.append(tracker)

            #離場的刪除 未離場的可以保留(送進以追蹤列表) < 3sec 超過3秒即刪除
        
    #取得所有box的追蹤資訊(by time)
    def get_tracking_result(self, gtime):
        tracking_results = []
        for tracker in self.tracker_list:
            result_box = tracker.get_result_box(gtime)
            #result_box = [[id, coord], [id, coord]]
            if len(result_box):
                tracking_results.append(result_box)
        return tracking_results

    #取得追蹤清單
    def get_tracker_list(self):
        #tracker_list = [] # [ [id,[[x1,... ,t], [x1,...,t], []]],  ]
        #for tracker in self.tracker_list:
        #    box_list = tracker.get_box_list()
        #    tracker_list.append(box_list)
        return self.tracker_list

    #評估候選結果
    def eval_campare(self, coord, gtime):
        #產生比較分數(水平偏差 垂直偏差 方向)
        eval_table = []
        for i in range(len(self.untrack_list)):
            tracker = self.untrack_list[i]
            #print('tracker:', tracker.id, ' compare with ', coord)
            comparison = tracker.campare_coord(coord, gtime)
            #print('comparison', comparison)
            eval_table.append([i, comparison])
        #print('eval table = ', eval_table)
        #過濾分數 過濾偏差>30?>15 時間差 > 3秒        
        new_eval_table = []
        for index, comparison in eval_table:
            if not self.is_out_specific(comparison):
                #沒超過規格要保留
                new_eval_table.append([index, comparison])
        eval_table = new_eval_table
        #print('new table=', eval_table)
        #指派id給tracker
        if len(eval_table) == 0:
            #如果 =0 建立新的 Tracker
            id = self.used_id #未來會用資料庫的id
            print('new tracker', id)
            self.used_id += 1
            tracker = Tracker(id)
            tracker.set_box(coord, gtime)
            #如果有場域資訊 替tracker 設定場域資訊
            if len(self.check_area_list) > 0:
                tracker.set_check_area(self.check_area_list)
                tracker.set_distance_matrix(self.distance_matrix)
            #加入已追蹤列表
            self.tracker_list.append(tracker)
        elif len(eval_table) == 1:
            # =1 表示只有一個最適合 
            #從trackerlist pop 出那個tracker
            tracker_index = eval_table[0][0] # [ [index, comparison],  ]
            tracker = self.untrack_list.pop(tracker_index)
            #print('find one tracker can', tracker.id)
            #指派box
            tracker.set_box(coord, gtime)
            #加入已追蹤列表
            self.tracker_list.append(tracker)
        else:
            #一個box有多個符合的tracker
            # >1 表示 可能有人重疊
            #eval_table >1 = [[5,[4,3]], [2,[1,-6]]]
            #多重比較
            # multi_eval_table row == col 找最近, 都很近=>比較方向
            # row != col 某人被某人遮擋 box可能要指派給多人
            # box_coord: [trackerid, trackerid]
            
            #直接分配最近的
            min_eval = -1
            table = []
            for index, comparison in eval_table:
                eval_sum = sum(comparison[0:3])
                if min_eval == -1 or eval_sum < min_eval:
                    min_eval = eval_sum
                    table = (index, comparison)

            #從trackerlist pop 出那個tracker
            tracker_index = table[0] # [index, comparison]
            tracker = self.untrack_list.pop(tracker_index)
            #print('find one tracker profit ', tracker.id)
            #指派box
            tracker.set_box(coord, gtime)
            #加入已追蹤列表
            self.tracker_list.append(tracker)

    #過濾比較分數
    def is_out_specific(self, comparison):
        #comparison = [右邊界偏差 上邊界偏差 左邊 下邊 方向速度]
        if (comparison[0] > 30 and comparison[1] > 30
            and comparison[2] > 30 and comparison[3] > 30 and comparison[4] < 3):
            return True
        else:
            return False

#儲存檢查點的資訊
class Check_Point():
    def __init__(self, id = -1, gtime = None, c_center = None) -> None:
        self.id = id
        self.gtime = gtime
        self.c_center = c_center
    
    def replace(self, cp):
        self.id = cp.id
        self.gtime = cp.gtime
        self.c_center = cp.c_center
    
    def reset(self, id, gtime, c_center):
        self.id = id
        self.gtime = gtime
        self.c_center = c_center

#儲存box資訊的基本單位，不參與評估，等待指派box
class Tracker():
    def __init__(self, id) -> None:
        self.box_list = []
        self.direct = 0 # 1 右下 2 右上 3 左下 4 左上
        #設定速度
        self.avg_v = 0
        #資料庫新增id
        self.id = id
        #設定檢查點
        self.check_area_list = [] #[ 0:[0, 0, 10, 10] , 1:[20, 20, 30, 30] ]
        #設定檢查點之間的實際距離[ [0 1], [1 0] ]
        self.distance_matrix = []
        #設定經過的上/上上一個檢查點位置
        self.check_point = Check_Point()
        self.last_check_point = Check_Point()
        
    #設定檢查點區域
    def set_check_area(self, check_area_list):
        self.check_area_list = check_area_list

    #設定檢查點之間的距離矩陣
    def set_distance_matrix(self, distance_matrix):
        self.distance_matrix = distance_matrix
        print()
        print(self.distance_matrix)
        print()

    #在哪個檢查點裡面
    def get_checkarea(self, c_center):
        #取得目前位置
        (cx, cy) = c_center
        #對每個區域測試
        for i in range(len(self.check_area_list)):
            (x1, y1, x2, y2) = self.check_area_list[i]
            if  (x1 < cx < x2) and (y1 < cy < y2):
                return i
        return -1

    #取得某個時間點的box
    def get_result_box(self, gtime):
        for ctime, coord in self.box_list[::-1]:
            if ctime == gtime:
                return [self.id, coord]
            elif ctime < gtime:
                return []
        return []

    #取得最新的box
    def get_last_box(self):
        return self.box_list[-1]
    
    #取得經過檢查點的點
    def get_passed_point(self):
        passed_list = []
        passed_list.append(self.check_point.c_center)
        passed_list.append(self.last_check_point.c_center)
        return passed_list

    #取得 bndbox 列表
    def get_box_list(self): #->[id, box_list]
        box_list = []
        for ctime, coord in self.box_list:
            box_list.append(coord)
        return [self.id, box_list]

    #計算中心點位置(約腳底位置)
    def count_center(self, coord):
        x1, y1, x2, y2 = coord
        return (int((x1+x2)/2), int((y1 + 19 * y2 ) / 20))

    #計算兩個楨(用索引當指定哪兩個楨)之間的平均像素速度， index2的時間 要是最新的喔
    def count_speed(self, index1, index2):
        try:
            #取得最新的有紀錄到 tracker 的時間
            ctime, ccoord = self.box_list[index2]
            #取得上一個有記錄到 tracker 的時間
            ptime, pcoord = self.box_list[index1]
        except IndexError:
            return (0.0, 0.0)
        #計算絕對距離 時間差
        c_center_x, c_center_y = self.count_center(ccoord)
        p_center_x, p_center_y = self.count_center(pcoord)
        dx = c_center_x - p_center_x
        dy = c_center_y - p_center_y
        t = ctime - ptime
        if t == 0:
            return (0.0, 0.0)
        #計算瞬間速度
        return (dx/t, dy/t)

    #取得瞬間像素速度(與前一張 frame 比)
    def get_piv(self):
        #-1 是最新的 -2是上一楨
        return self.count_speed(-2, -1)

    #取得平均像素速度(沒檢查點的話就是出現到現在的位置)
    def get_pav(self):
        #0是最初也最
        return self.count_speed(0, -1)
    
    #取得平均速度
    def get_avg_v(self):
        if len(self.check_area_list) < 2:
            return 0.0
        gtime, coord = self.get_last_box()
        avg_v = self.count_avg(gtime, coord)
        if avg_v:
            #有計算出平均速度
            self.avg_v = avg_v
        return self.avg_v

    #檢查有沒有在檢查點 有的話計算平均速度
    def count_avg(self, gtime, coord):
        (t, d, avg) = (0.0, 0.0, 0.0)
        #看這個座標有沒有在檢查點裡面
        c_center = self.count_center(coord)
        check_point_now_id = self.get_checkarea(c_center)
        #print('track id=',self.id, 'check_point_now:', check_point_now_id)
        if check_point_now_id != -1 and check_point_now_id != self.check_point.id:
            #經過新的檢查點，可能是第一次經過，不計算平均速度
            if self.check_point.id != -1:
                #有經過上上個檢查點，不是第一次，計算平均速度
                t = gtime - self.check_point.gtime
                #真實距離
                gd = self.distance_matrix[self.check_point.id][check_point_now_id]
                #像素距離
                pd = self.distance_matrix[check_point_now_id][self.check_point.id]
                if self.check_point.id > check_point_now_id:
                    gd, pd = pd, gd
                #距離像素比
                dr = gd / pd
                d = dr * self.count_abs_pd(c_center, self.check_point.c_center)
                avg = d/t

            #檢查點更新 -1 -> 0(第一次) or 1 -> 2(第二次以上)， 紀錄經過檢查點的時間
            self.last_check_point.replace(self.check_point)
            self.check_point.reset(check_point_now_id, gtime, c_center)
        return avg
    
    #計算兩點像素絕對距離
    def count_abs_pd(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx * dx + dy * dy)

    #儲存框,足跡,速度
    def set_box(self, coord, gtime):
        self.box_list.append([gtime, coord])

    #與上一個框比較 計算新方向 回傳給管理者評估要不要指派框 
    def campare_coord(self, coord, gtime):
        last_time, last_coord = self.get_last_box()
        ld = coord[0] - last_coord[0] #x1 - x1
        rd = coord[2] - last_coord[2] #x2 - x2
        ud = coord[1] - last_coord[1] #y1 - y1
        dd = coord[3] - last_coord[3] #y2 - y2
        td = gtime - last_time
        return [abs(ld), abs(ud), abs(rd), abs(dd), td]

    #計算目前與上一個box的時間差
    def count_time_diff(self, gtime):
        last_time, last_coord = self.get_last_box()
        return gtime - last_time

    #位置相近時間差距大 > 2sec

    #人可能離開 刪除追蹤者並上傳資料到資料庫 回傳要求刪除的信號