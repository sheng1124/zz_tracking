#管理追蹤者 管理並指派框給追蹤者
#一個box至少指派一個tracker
#一個tracker只能指派一個box
class Tracker_manager():
    def __init__(self) -> None:
        self.tracker_list=[]
        self.untrack_list = []
        self.used_id = 0
        #檢查點設定

    def input_boxs(self, results, gtime, shape):
        #收到新的辨識結果 重置追蹤列表 變為未追蹤狀態
        self.untrack_list, self.tracker_list = self.tracker_list, self.untrack_list
        #評估每一個box 並指派給tracker 同時把追蹤過的tracker放進已追蹤列表
        h, w = int(shape[0]), int(shape[1])
        for box in results: 
            #ex: (x1, y1, x2, y2) = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
            print('evaluate', box, 'time', gtime)
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

    #評估候選結果
    def eval_campare(self, coord, gtime):
        #產生比較分數(水平偏差 垂直偏差 方向)
        eval_table = []
        for i in range(len(self.untrack_list)):
            tracker = self.untrack_list[i]
            print('tracker:', tracker.id, ' compare with ', coord)
            comparison = tracker.campare_coord(coord, gtime)
            print('comparison', comparison)
            eval_table.append([i, comparison])
        print('eval table = ', eval_table)
        #過濾分數 過濾偏差>30?>15 時間差 > 3秒        
        new_eval_table = []
        for index, comparison in eval_table:
            if not self.is_out_specific(comparison):
                #沒超過規格要保留
                new_eval_table.append([index, comparison])
        eval_table = new_eval_table
        print('new table=', eval_table)
        #指派id給tracker
        if len(eval_table) == 0:
            #如果 =0 建立新的 Tracker
            id = self.used_id #未來會用資料庫的id
            print('new tracker', id)
            self.used_id += 1
            tracker = Tracker(id)
            tracker.set_box(coord, gtime)
            #加入已追蹤列表
            self.tracker_list.append(tracker)
        elif len(eval_table) == 1:
            # =1 表示只有一個最適合 
            #從trackerlist pop 出那個tracker
            tracker_index = eval_table[0][0] # [ [index, comparison],  ]
            tracker = self.untrack_list.pop(tracker_index)
            print('find one tracker can', tracker.id)
            #指派box
            tracker.set_box(coord, gtime)
            #加入已追蹤列表
            self.tracker_list.append(tracker)
        else:
            # >1 表示 可能有人重疊
            #eval_table >1 = [[5,[4,3]], [2,[1,-6]]]
            #多重比較
            # multi_eval_table row == col 找最近, 都很近=>比較方向
            # row != col 某人被某人遮擋 box可能要指派給多人
            # box_coord: [trackerid, trackerid]
            pass
    
    #過濾比較分數
    def is_out_specific(self, comparison):
        #comparison = [右邊界偏差 上邊界偏差 左邊 下邊 方向速度]
        if (comparison[0] > 100 and comparison[1] > 100 
            and comparison[2] > 100 and comparison[3] > 100 and comparison[4] < 3):
            return True
        else:
            return False
        

#儲存box資訊的基本單位，不參與評估，等待指派box
class Tracker():
    def __init__(self, id) -> None:
        self.box_list = []
        self.direct = 0 # 1 右下 2 右上 3 左下 4 左上
        #設定速度
        self.avg_v = 0
        #資料庫新增id
        self.id = id
    
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

    #檢查有沒有在檢查點 有的話計算平均速度

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