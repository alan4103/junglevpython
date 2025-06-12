import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from datetime import datetime
from io import BytesIO
import mysql.connector
from mysql.connector import Error
from openpyxl import Workbook

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 用於 flash 消息

# MySQL 數據庫配置
DB_CONFIG = {
    'host': '172.245.146.23',
    'user': 'workrecord',           # 替換為您的 MySQL 用戶名
    'password': 'Ylbbqs1236',   # 替換為您的 MySQL 密碼
    'database': 'workrecord'  # 使用您指定的數據庫名稱
}

# 初始化數據庫連接
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        flash(f"數據庫連接錯誤: {e}", 'error')
        return None

# 初始化數據庫表
def init_db():
    connection = None
    try:
        # 先連接服務器不指定數據庫
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = connection.cursor()
        
        # 創建數據庫如果不存在
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        connection.commit()
        flash("數據庫初始化成功", 'success')
    except Error as e:
        flash(f"數據庫初始化失敗: {e}", 'error')
        if connection:
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 獲取所有記錄
def get_all_records():
    records = []
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, job_number, department, work_type, 
                       line_count, remark, record_time, date 
                FROM work_records 
                ORDER BY date DESC, record_time DESC
            """)
            records = cursor.fetchall()
        except Error as e:
            flash(f"獲取記錄失敗: {e}", 'error')
        finally:
            cursor.close()
            connection.close()
    return records

# 搜尋記錄
def search_records(keyword):
    records = []
    connection = get_db_connection()
    if connection:
        try:
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
            flash(f"搜索記錄失敗: {e}", 'error')
        finally:
            cursor.close()
            connection.close()
    return records

# 新增記錄
def add_record(job_number, department, work_type, line_count, remark, date):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
                INSERT INTO work_records 
                (job_number, department, work_type, line_count, remark, date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (job_number, department, work_type, line_count, remark, date))
            connection.commit()
            flash("記錄添加成功", 'success')
            return cursor.lastrowid
        except Error as e:
            flash(f"添加記錄失敗: {e}", 'error')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()
    return None

# 更新記錄
def update_record(record_id, job_number, department, work_type, line_count, remark, date):
    connection = get_db_connection()
    if connection:
        try:
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
            if cursor.rowcount > 0:
                flash("記錄更新成功", 'success')
                return True
            else:
                flash("沒有找到要更新的記錄", 'warning')
                return False
        except Error as e:
            flash(f"更新記錄失敗: {e}", 'error')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()
    return False

# 刪除記錄
def delete_record(record_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "DELETE FROM work_records WHERE id = %s"
            cursor.execute(query, (record_id,))
            connection.commit()
            if cursor.rowcount > 0:
                flash("記錄刪除成功", 'success')
                return True
            else:
                flash("沒有找到要刪除的記錄", 'warning')
                return False
        except Error as e:
            flash(f"刪除記錄失敗: {e}", 'error')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()
    return False

# 下載 Excel 文件
@app.route('/download')
def download_excel():
    try:
        records = get_all_records()
        
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
    except Exception as e:
        flash(f"生成Excel文件失敗: {e}", 'error')
        return redirect(url_for('view_records'))

@app.route('/')
def index():
    init_db()  # 確保數據庫已初始化
    default_date = datetime.now().strftime('%Y-%m-%d')
    work_types = ['安裝', '維修', '收機']
    return render_template('index.html', default_date=default_date, work_types=work_types)

@app.route('/add', methods=['POST'])
def add():
    job_number = request.form.get('job_number', '').strip()
    department = request.form.get('department', '').strip()
    work_type = request.form.get('work_type', '安裝').strip()
    line_count = request.form.get('line_count', '0').strip()
    remark = request.form.get('remark', '').strip()
    date = request.form.get('date', '').strip()
    
    # 驗證必填字段
    if not job_number:
        flash("工作單號不能為空", 'error')
        return redirect(url_for('index'))
    if not date:
        flash("日期不能為空", 'error')
        return redirect(url_for('index'))
    
    # 轉換線數為整數
    try:
        line_count = int(line_count) if line_count else 0
    except ValueError:
        line_count = 0
    
    add_record(job_number, department, work_type, line_count, remark, date)
    return redirect(url_for('view_records'))

@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit(record_id):
    if request.method == 'POST':
        job_number = request.form.get('job_number', '').strip()
        department = request.form.get('department', '').strip()
        work_type = request.form.get('work_type', '安裝').strip()
        line_count = request.form.get('line_count', '0').strip()
        remark = request.form.get('remark', '').strip()
        date = request.form.get('date', '').strip()
        
        # 驗證必填字段
        if not job_number:
            flash("工作單號不能為空", 'error')
            return redirect(url_for('edit', record_id=record_id))
        if not date:
            flash("日期不能為空", 'error')
            return redirect(url_for('edit', record_id=record_id))
        
        # 轉換線數為整數
        try:
            line_count = int(line_count) if line_count else 0
        except ValueError:
            line_count = 0
        
        update_record(record_id, job_number, department, work_type, line_count, remark, date)
        return redirect(url_for('view_records'))
    
    # GET 請求處理
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM work_records WHERE id = %s", (record_id,))
            record = cursor.fetchone()
            
            if not record:
                flash("找不到指定的記錄", 'error')
                return redirect(url_for('view_records'))
            
            work_types = ['安裝', '維修', '收機']
            return render_template('edit.html', record=record, work_types=work_types)
        except Error as e:
            flash(f"獲取記錄失敗: {e}", 'error')
            return redirect(url_for('view_records'))
        finally:
            cursor.close()
            connection.close()
    return redirect(url_for('view_records'))

@app.route('/delete/<int:record_id>')
def delete(record_id):
    delete_record(record_id)
    return redirect(url_for('view_records'))

@app.route('/records')
def view_records():
    keyword = request.args.get('search', '').strip()
    if keyword:
        records = search_records(keyword)
    else:
        records = get_all_records()
    return render_template('records.html', records=records, search_keyword=keyword)

if __name__ == '__main__':
    init_db()  # 啟動時初始化數據庫
    app.run(debug=True)