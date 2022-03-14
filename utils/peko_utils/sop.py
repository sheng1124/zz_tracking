import mysql.connector

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
    print(type(cursor))
    results = []
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        connection.commit()
        cursor.close()
    except Exception as e:
        print("查詢資料庫失敗", e)
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


