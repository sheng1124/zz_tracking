import mysql.connector

import time

#連結到資料庫
def connect_db(database, host = '127.0.0.1', port = 3306, user='root', password=''):
    connection = None
    try:
        connection = mysql.connector.connect(host=host, port=port, database=database, user=user, password=password)
    except Exception as e:
        print("無法連接道資料庫", e)
    return connection

#關閉資料庫連線
def close_db(connection:mysql.connector.connection_cext.CMySQLConnection):
    if connection.is_connected():
        connection.close()
        print("資料庫連線已關閉")

#查詢資料
def query_db(connection:mysql.connector.connection_cext.CMySQLConnection, sql:str):
    cursor = connection.cursor()
    results = []
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        connection.commit()
        cursor.close()
    except Exception as e:
        print("查詢資料庫失敗", e)
    return results

#執行 sql 指令 不例外處理
def execute_sql(connection:mysql.connector.connection_cext.CMySQLConnection, sql:str):
    cursor = connection.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    connection.commit()
    cursor.close()
    return results

#取得資料庫版本、目前使用的資料庫
def all_db_info(connection:mysql.connector.connection_cext.CMySQLConnection):
    try:
        db_info = connection.get_server_info()
        cursor = connection.cursor()
        cursor.execute('select database()')
        record = cursor.fetchone()
        connection.commit()
        cursor.close()
        return [db_info, record]
    except Exception as e:
        print('無法取的資料庫版本')

#插入資料
def insert_data(connection:mysql.connector.connection_cext.CMySQLConnection, sql:str):
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
        connection.commit()
        cursor.close()
    except Exception as e:
        print("插入資料庫失敗", e)

#建立 bounding box 表
def new_box_table(connection:mysql.connector.connection_cext.CMySQLConnection, table_name):
    sql = 'CREATE TABLE {} ( `box_id` INT NOT NULL AUTO_INCREMENT , `coordinate` VARCHAR(100) NOT NULL , `time` DATETIME NOT NULL , `gtime` DOUBLE NOT NULL , `track_id` INT NOT NULL ,`imgpath` VARCHAR(200) NOT NULL , PRIMARY KEY (`box_id`)) ENGINE = InnoDB'.format(table_name)
    cursor = connection.cursor()
    cursor.execute(sql)
    connection.commit()
    cursor.close()

#插入 bounding box 資料
def insert_box(connection:mysql.connector.connection_cext.CMySQLConnection, table_name, box_data):
    sql = 'insert into {} (box_id, coordinate, time, gtime, track_id, imgpath) values ({}, "{}", {}, {}, {}, "{}")'.format(table_name, *box_data)
    insert_data(connection, sql)

#插入平均速度資料
def insert_avg_speed(connection:mysql.connector.connection_cext.CMySQLConnection, avs_data):
    sql = 'insert into average_speed (event_id, track_id, site, datetime, start_time, end_time, move_distance, avg_speed) values ({}, {}, "{}", {}, {}, {}, {}, {})'.format(*avs_data)
    insert_data(connection, sql)

#取得最新的 tracker id
def query_last_tracker_id(connection:mysql.connector.connection_cext.CMySQLConnection, table_name):
    sql = 'SELECT track_id FROM {} ORDER BY track_id DESC LIMIT 1'.format(table_name)
    results = query_db(connection, sql)
    if len(results):
        return results[0][0]
    else:
        return 0


if __name__ == '__main__':
    conn = connect_db('konpeko')
    #new_box_table(conn, 'cgu_box')
    id = query_last_tracker_id(conn, 'average_speed')

    print(id)

    d = (0, 10, 'cgu', '20220304135717', 1646373437.910015, 1646373438.7266257, 1.712508672714728, 2.0970934319545296)
    insert_avg_speed(conn,d)

    close_db(conn)