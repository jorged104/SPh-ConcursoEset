import MySQLdb
 
DB_HOST = 'localhost' 
DB_USER = 'root' 
DB_PASS = '' 
DB_NAME = 'pg' 

def run_query(query=''): 
    datos = [DB_HOST, DB_USER, DB_PASS, DB_NAME] 
 
    conn = MySQLdb.connect(*datos)  #Abriendo Conexion 
    cursor = conn.cursor()         
    cursor.execute(query)          
 
    if query.upper().startswith('SELECT'): 
        data = cursor.fetchall()   
    else: 
        conn.commit()               
        data = None 
 
    cursor.close()                 
    conn.close()                   # Cerrar la conexión 
 
    return data

res = run_query("SELECT email from datos")
print (res) 