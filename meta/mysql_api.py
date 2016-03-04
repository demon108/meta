import MySQLdb

def connect(dbname,host='192.168.241.32'):
    conn = MySQLdb.connect(user='oopin',passwd='OOpin2007Group',db=dbname,host=host);
    return conn

def close(conn):
    conn.cursor().close()
    conn.close()
    
def query_many(conn,sql):
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    except:
        raise Exception('sql error') 

def insert(conn,sql):
    try:
        cursor = conn.cursor()
        num = cursor.execute(sql)
        return num
    except:
        pass

def commit(conn):
    conn.commit()


if __name__ == "__main__":
    #conn_local = connect('meta',host='localhost')
    conn_local = connect('meta',host='192.168.241.17')    
    conn_local.close()
