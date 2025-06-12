import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime
from io import BytesIO
import mysql.connector
from mysql.connector import Error
from openpyxl import Workbook

app = Flask(__name__)

# MySQL 數據庫配置
DB_CONFIG = {
    'host': 'workrecord:Ylbbqs1236@junglevproject-worksql-k1jaa3:3306/workrecord',
    'user': 'workrecord',  # 替換為你的 MySQL 用戶名
    'password': 'Ylbbqs1236',  # 替換為你的 MySQL 密碼
    'database': 'workrecord'  # 數據庫名稱
}

# 初始化數據庫連接
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# 初始化數據庫表
def init_db():
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # 檢查數據庫是否存在，不存在則創建
            cursor.execute("CREATE DATABASE IF NOT EXISTS work_records_db")
            cursor.execute("USE work_records_db")
            
            # 創建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    job_number VARCHAR(50) NOT NULL,
                    department VARCHAR(50),
                    work_type ENUM('安裝', '維修', '收機') NOT NULL,
                    line_count INT,
                    remark TEXT,
                    record_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date DATE NOT NULL
                )
            """)
            connection.commit()
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 獲取所有記錄
def get_all_records():
    records = []
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, job_number, department, work_type, 
                       line_count, remark, record_time, date 
                FROM work_records 
                ORDER BY date DESC, record_time DESC
            """)
            records = cursor.fetchall()
    except Error as e:
        print(f"Error fetching records: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    return records

# 搜尋記錄
def search_records(keyword):
    records = []
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, job_number, department, work_type, 
                       line_count, remark, record_time, date 
                FROM work_records 
                WHERE job_number LIKE %s OR 
                      department LIKE %s OR 
                      work_type LIKE %s OR 
                      remark LIKE %s
                ORDER BY date DESC, record_time DESC
            """
            search_param = f"%{keyword}%"
            cursor.execute(query, (search_param, search_param, search_param, search_param))
            records = cursor.fetchall()
    except Error as e:
        print(f"Error searching records: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    return records

# 新增記錄
def add_record(job_number, department, work_type, line_count, remark, date):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            query = """
                INSERT INTO work_records 
                (job_number, department, work_type, line_count, remark, date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (job_number, department, work_type, line_count, remark, date))
            connection.commit()
            return cursor.lastrowid
    except Error as e:
        print(f"Error adding record: {e}")
        connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    return None

# 更新記錄
def update_record(record_id, job_number, department, work_type, line_count, remark, date):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            query = """
                UPDATE work_records 
                SET job_number = %s, 
                    department = %s, 
                    work_type = %s, 
                    line_count = %s, 
                    remark = %s, 
                    date = %s 
                WHERE id = %s
            """
            cursor.execute(query, (job_number, department, work_type, line_count, remark, date, record_id))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error updating record: {e}")
        connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    return False

# 刪除記錄
def delete_record(record_id):
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            query = "DELETE FROM work_records WHERE id = %s"
            cursor.execute(query, (record_id,))
            connection.commit()
            return cursor.rowcount > 0
    except Error as e:
        print(f"Error deleting record: {e}")
        connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    return False

# 下載 Excel 文件
@app.route('/download')
def download_excel():
    try:
        # 獲取所有記錄
        records = get_all_records()
        
        # 創建 Excel 文件
        wb = Workbook()
        ws = wb.active
        ws.append(['ID', '工作單號', '部門', '工作類型', '線數', '備註', '記錄時間', '日期'])
        
        for record in records:
            ws.append([
                record['id'],
                record['job_number'],
                record['department'],
                record['work_type'],
                record['line_count'],
                record['remark'],
                record['record_time'].strftime('%Y-%m-%d %H:%M:%S'),
                record['date'].strftime('%Y-%m-%d')
            ])
        
        file_stream = BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        
        return send_file(
            file_stream,
            as_attachment=True,
            download_name='work_records.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Error as e:
        print(f"Error generating Excel: {e}")
        return redirect(url_for('view_records'))

@app.route('/')
def index():
    init_db()  # 確保數據庫已初始化
    default_date = datetime.now().strftime('%Y-%m-%d')
    work_types = ['安裝', '維修', '收機']
    return render_template('index.html', default_date=default_date, work_types=work_types)

@app.route('/add', methods=['POST'])
def add():
    job_number = request.form.get('job_number')
    department = request.form.get('department')
    work_type = request.form.get('work_type')
    line_count = request.form.get('line_count', type=int)
    remark = request.form.get('remark')
    date = request.form.get('date')
    
    if job_number and date:
        add_record(job_number, department, work_type, line_count, remark, date)
    return redirect(url_for('view_records'))

@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit(record_id):
    if request.method == 'POST':
        job_number = request.form.get('job_number')
        department = request.form.get('department')
        work_type = request.form.get('work_type')
        line_count = request.form.get('line_count', type=int)
        remark = request.form.get('remark')
        date = request.form.get('date')
        
        update_record(record_id, job_number, department, work_type, line_count, remark, date)
        return redirect(url_for('view_records'))
    
    # GET 請求時顯示編輯表單
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM work_records WHERE id = %s"
            cursor.execute(query, (record_id,))
            record = cursor.fetchone()
            
            if not record:
                return redirect(url_for('view_records'))
            
            work_types = ['安裝', '維修', '收機']
            return render_template('edit.html', record=record, work_types=work_types)
    except Error as e:
        print(f"Error fetching record for edit: {e}")
        return redirect(url_for('view_records'))
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/delete/<int:record_id>')
def delete(record_id):
    delete_record(record_id)
    return redirect(url_for('view_records'))

@app.route('/records')
def view_records():
    keyword = request.args.get('search', '')
    if keyword:
        records = search_records(keyword)
    else:
        records = get_all_records()
    return render_template('records.html', records=records, search_keyword=keyword)

if __name__ == '__main__':
    init_db()  # 啟動時初始化數據庫
    app.run(debug=True)