import sqlite3
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from time import time 
def get_connection():
    conn = sqlite3.connect("my_dpython --veata.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def buttons_data():
    conn=get_connection()
    cur=conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS button_data(id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT, file_id TEXT, parent TEXT ,FOREIGN KEY (parent) REFERENCES button_data(id) ON DELETE CASCADE) """)
    conn.commit()
    conn.close()

def files_data():
      
      conn=get_connection()
      cur=conn.cursor()
      cur.execute("""CREATE TABLE IF NOT EXISTS file_data(id INTEGER PRIMARY KEY AUTOINCREMENT,file_id TEXT, button_id INTEGER 

                                  ,file_name TEXT,FOREIGN KEY (button_id) REFERENCES button_data(id) ON DELETE CASCADE )""")
      
      conn.commit()
      conn.close()

def admins_data():
      conn=get_connection()
      cur=conn.cursor()
      cur.execute("CREATE TABLE IF NOT EXISTS admin_data(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,user_name TEXT) ")
      conn.commit()
      conn.close()

def links_data():
      conn=get_connection()
      cur=conn.cursor()
      cur.execute("CREATE TABLE IF NOT EXISTS links(id INTEGER PRIMARY KEY AUTOINCREMENT, link TEXT , unique_id TEXT,created_at INTEGER,is_downloading INTEGER DEFAULT 0)")
      conn.commit()
      conn.close()

def user_data():
      conn=get_connection()
      cur=conn.cursor()
      cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY  ,username TEXT , language TEXT DEFAULT 'ar' )")
      conn.commit()
      conn.close()

buttons_data()
files_data()
admins_data()
links_data()
user_data()

def upload_file(parent_id,file_id:str,doc_name:str):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("INSERT INTO file_data (file_id,button_id,file_name) VALUES (?,?,?) ",(file_id,parent_id,doc_name))
        conn.commit()
        conn.close()

def get_file_name_of(id:str):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("SELECT title FROM button_data WHERE parent = ? ",(id,))
        result=cur.fetchone()
        conn.close()
        return result

def get_buttons_by_parent(parent_id):
    conn = get_connection()
    cur = conn.cursor()
    is_root = parent_id is None or str(parent_id).upper() in ["NONE", "NULL"]

    if is_root:
       
       cur.execute("SELECT id, title FROM button_data WHERE parent IS NULL")
    else:
        try:
                cur.execute("SELECT id, title FROM button_data WHERE parent = ?", (int(parent_id),))
        except ValueError:
              cur.execute("SELECT id, title FROM button_data WHERE parent IS NULL")

    children = cur.fetchall()
    print(f"DEBUG DB: Found {len(children)} items for parent {parent_id}") #Debug
    conn.close()
    return children


def get_parent_of(current_menu_id):    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT parent FROM button_data WHERE id = ?", (current_menu_id,))
    result = cur.fetchone()
    conn.close()
    
    if result and result[0] is not None:
        return str(result[0])
    
    return None # Return the string NULL if we hit the top

def create_inline_button(name,parent_id):
        conn=get_connection()
        cur=conn.cursor()
        is_root = parent_id is None or str(parent_id).upper() in ["NONE", "NULL"]
        if is_root: 
              parent_id=None
        else:
              parent_id=int(parent_id)

        cur.execute("INSERT INTO button_data (title, parent) VALUES (?, ?)",(name,parent_id))
        conn.commit()
        conn.close()
        
def get_files_ids(parent_id):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("SELECT id,file_id,file_name FROM file_data  WHERE button_id = ? ",(parent_id,))
        results=cur.fetchall()
        conn.close()
        return results

def delete_button_by_id(parent_id):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("DELETE FROM button_data WHERE id=?",[parent_id])
        conn.commit()
        conn.close()

def remove_uploaded_file(parent_id):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("DELETE FROM file_data WHERE button_id= ? ",[parent_id])
        conn.commit()
        conn.close()

def remame_button(new_name,parent_id):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("UPDATE button_data SET title =? where id =?",(new_name,parent_id))
        conn.commit()
        conn.close()

#admins section 
def add_admin(user_id,user_name):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("INSERT INTO admin_data (user_id,user_name) VALUES (?,?) ",(user_id,user_name))
        conn.commit()
        conn.close()

def remove_admin(user_id):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("DELETE FROM admin_data WHERE user_id = ?",(user_id,))
        conn.commit()
        conn.close()

def get_admin_ids():
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("SELECT user_id FROM admin_data")
        admins = [str(row[0]) for row in cur.fetchall()]
        conn.close()
        return admins

def get_admin_info():
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("SELECT user_id,user_name FROM admin_data")
        admins =cur.fetchall()
        conn.close()
        return admins

#links table , download feature 
def add_link(link:str ,unique_id:str):
        conn=get_connection()
        cur=conn.cursor()
        created_at=time()
        cur.execute("INSERT INTO LINKS(link,unique_id,created_at) VALUES (?,?,?)",(link,unique_id,created_at))
        conn.commit()
        conn.close()

def get_link_by_id(unique_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT link FROM LINKS WHERE unique_id = ?", (unique_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    return row[0] if row else None

def cleanup_func():
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("DELETE FROM LINKS WHERE created_at < unixepoch('now') - 1200;")
        conn.commit()
        conn.close()

def download_flag(unique_id:str):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("SELECT is_downloading FROM LINKS WHERE unique_id=?",(unique_id,))
        is_downloading=cur.fetchone()
        
        if not is_downloading:
               return None
        
        if is_downloading[0] == 0 :
              
              cur.execute("UPDATE links SET is_downloading = 1 WHERE unique_id = ?", (unique_id,))
              conn.commit()
              return False
        
        conn.close()
        return True

def reset_downlaod_flag(unique_id:str):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("UPDATE links SET is_downloading = 0 WHERE unique_id = ?", (unique_id,))
        conn.commit()
        conn.close()

#users table , when some one message the bot for the first time save his inforamtion in the data base

def add_user(user_id : int ,username :str = None , language : str ="ar"):
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (user_id, username, language) VALUES (?, ?, ?)",(user_id, username, language))
        conn.commit()
        conn.close()

def get_users():
        conn=get_connection()
        cur=conn.cursor()
        cur.execute("SELECT user_id FROM users")
        for row in cur.fetchall():
               yield row[0]     

def mark_user_as_inactive(user_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))

#language 

def get_user_language(user_id: int) -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
 
    if row and row[0]:
        return row[0]
    return "ar"


def update_user_language(user_id: int, new_lang: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET language = ? WHERE user_id = ?", (new_lang, user_id))
    conn.commit()
    conn.close()