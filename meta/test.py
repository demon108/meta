import mysql_api as mysql

conn_local = mysql.connect('meta',host='localhost')
conn_local_cursor = conn_local.cursor()
conn_local.set_character_set('utf8')
conn_local_cursor.execute('set names utf8mb4')
conn_local_cursor.execute('SET CHARACTER SET utf8;')
conn_local_cursor.execute('SET character_set_connection=utf8;')
conn_local_cursor.execute('set interactive_timeout=24*3600;')
conn_local_cursor.execute('set wait_timeout=24*3600;')
conn_local_cursor.execute('set innodb_lock_wait_timeout=1000;')

sql = 'select * from meta_result limit 1;'
conn_local_cursor.execute(sql)
print conn_local_cursor.fetchall()
conn_local.close()
