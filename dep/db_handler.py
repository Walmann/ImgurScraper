import sqlite3 as sql



database_name = 'file_db.db'

class DB_handler:
    @staticmethod

    def create_new_database():
        DB_handler.runQuerry("CREATE TABLE IF NOT EXISTS FILESDB (StringX TEXT, file_path TEXT, file_size INT, was_image BOOL, response_code INT, message TEXT);",[])
        return

    def runQuerry(querry, values):
        # if values:
        #      if values[4] == 200:  
        #         pass
        conn = sql.connect(database_name, check_same_thread=False)
        cur = conn.cursor()
        if values:
            cur.execute(querry, values)
        else:
            cur.execute(querry)
        result = cur.fetchall()
        conn.commit()
        conn.close()
        return result
        # SQLDB = sql.connect(database_name) 
        # cur = SQLDB.cursor()
        # temp = cur.execute(querry, values)
        # # temp2 = cur.fetchall()
        
        # return temp
    



    def fetch_last_combination():
        # data = DB_handler.runQuerry("select * from FILESDB", ())
        # for row in data:
        #     print(row)
        query = "SELECT * FROM FILESDB ORDER BY StringX DESC LIMIT 1"
        data = DB_handler.runQuerry(query, ())
        # tuple_data = tuple(data[0][0])
        tuple_data = tuple(data[0][0]) if data else None
        return tuple_data
    
    def submit_new_stringX(StringX = "", file_path = "", file_size = 0, was_image = False, response_code = 0, message="Empty", **kwargs):
        """Submit new StringX

        Args:
            StringX (str, optional): Defaults to "".\n
            file_path (str, optional): Defaults to "".\n
            file_size (int, optional): Defaults to 0.\n
            was_image (bool, optional): Defaults to False.\n
            response_code (int, optional): Defaults to 0.\n
            message (str, optional): Defaults to "".
        """


        # query = f"INSERT INTO FILESDB ({StringX}, '{file_path}', {int(file_size)}, {was_image}, {response_code}, {message}) values(?, ?, ?, ?, ?, ?)"
        query = "INSERT INTO FILESDB (StringX, file_path, file_size, was_image, response_code, message) values(?, ?, ?, ?, ?, ?)"
        values = (StringX, file_path, int(file_size), was_image, response_code, message)
        DB_handler.runQuerry(query, values)
        # data = DB_handler.runQuerry(query)
        return
    
    def search_for_string(string):
        query = f"SELECT * FROM FILESDB WHERE StringX LIKE '{string}'"
        data = DB_handler.runQuerry(query, [])
        temp= len(data)
        
        return True if temp >= 1 else None
