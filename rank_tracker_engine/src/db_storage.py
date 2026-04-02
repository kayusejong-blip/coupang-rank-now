import sqlite3
import datetime

class DBStorage:
    def __init__(self, db_path="ranking_history.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS rank_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            product_id TEXT,
            product_name TEXT,
            rank INTEGER,
            rank_incl_ad INTEGER,
            ad_status TEXT,
            rocket_status TEXT,
            timestamp TEXT
        )
        '''
        self.conn.execute(query)
        self.conn.commit()

    def insert_record(self, keyword, data):
        # 지정된 형식 Timestamp: 2026-02-26 14:00 구조 생성
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = '''
        INSERT INTO rank_history (
            keyword, product_id, product_name, rank, rank_incl_ad, ad_status, rocket_status, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (
            keyword,
            data['Product_ID'],
            data['Product_Name'],
            data['Rank'],
            data['Rank_Incl_Ad'],
            data['Ad_Status'],
            data['Rocket_Status'],
            timestamp
        ))
        self.conn.commit()

    def fetch_all(self):
        cursor = self.conn.execute("SELECT * FROM rank_history ORDER BY id DESC")
        return cursor.fetchall()
