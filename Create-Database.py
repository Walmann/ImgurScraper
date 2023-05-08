# This scrip is just for development. I have already ran this script without creating a SQL DB, so I'm using this script to do it.
from sqlite3 import sql
import os
from setup import setup_variables

settings = setup_variables()

con = sql.connect('file_db.db')
with con:
    con.execute("""
        CREATE TABLE IF NOT EXISTS FILESDB (
            StringX TEXT,
            file_path TEXT
        );
    """)
print("Creating and updating Database")
for root, dirs, files in os.walk(settings["download_folder"]):
    for dir in dirs:
        
        for file in files:
            file_name = file.split(".")[0]
            # file_path = os.path.join(dir, file)
            sqlquerry = "INSERT INTO FILESDB (StringX, file_path) values(?, ?)"
            con.execute(sqlquerry, (file_name, file))

