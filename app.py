import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from datetime import datetime
from io import BytesIO
import mysql.connector
from mysql.connector import Error
from openpyxl import Workbook
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL 數據庫配置
DB_CONFIG = {
    'host': '172.245.146.23',
    'user': 'workrecord',
    'password': 'Ylbbqs1236',
    'database': 'workrecord'
}

# 初始化數據庫連接
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        flash(f"數據庫連接錯誤: {e}", 'error')
        return None

# 獲取產品價格
def get_product_prices():
    prices = {}
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT product_code, price FROM product_prices")
            for row in cursor.fetchall():
                prices[row['product_code']] = float(row['price'])
        except Error as e:
            flash(f"獲取產品價格失敗: {e}", 'error')
        finally:
            cursor.close()
            connection.close()
    return prices

# 新增記錄（包含多個產品）
def add_record(job_number, department, work_type, line_count, products, remark, date):
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = None
    record_id = None
    try:
        cursor = connection.cursor()
        
        # 插入主記錄
        cursor.execute("""
            INSERT INTO work_records 
            (job_number, department, work_type, line_count, remark, date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (job_number, department, work_type, line_count, remark, date))
        
        record_id = cursor.lastrowid
        
        # 插入產品記錄
        for product_code, quantity in products.items():
            cursor.execute("""
                INSERT INTO record_products 
                (record_id, product_code, quantity)
                VALUES (%s, %s, %s)
            """, (record_id, product_code, quantity))
        
        connection.commit()
        flash("記錄添加成功", 'success')
    except Error as e:
        connection.rollback()
        flash(f"添加記錄失敗: {e}", 'error')
    finally:
        if cursor:
            cursor.close()
        connection.close()
    return record_id

# 獲取所有記錄（包含產品信息）
def get_all_records():
    records = []
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 獲取主記錄
            cursor.execute("""
                SELECT id, job_number, department, work_type, 
                       line_count, remark, record_time, date 
                FROM work_records 
                ORDER BY date DESC, record_time DESC
            """)
            records = cursor.fetchall()
            
            # 獲取每個記錄的產品信息
            for record in records:
                cursor.execute("""
                    SELECT product_code, quantity 
                    FROM record_products 
                    WHERE record_id = %s
                """, (record['id'],))
                products = cursor.fetchall()
                record['products'] = products
                
                # 計算總金額
                total = 0
                product_prices = get_product_prices()
                for product in products:
                    total += product_prices.get(product['product_code'], 0) * product['quantity']
                record['total_amount'] = total
                
        except Error as e:
            flash(f"獲取記錄失敗: {e}", 'error')
        finally:
            cursor.close()
            connection.close()
    return records

# 其他CRUD操作（更新、刪除等）也需要相應修改...
# 這裡省略，實際應用中需要補充完整

@app.route('/')
def index():
    product_prices = get_product_prices()
    default_date = datetime.now().strftime('%Y-%m-%d')
    work_types = ['安裝', '維修', '收機']
    return render_template('index.html', 
                         default_date=default_date,
                         work_types=work_types,
                         product_prices=product_prices)

@app.route('/add', methods=['POST'])
def add():
    try:
        # 獲取基本表單數據
        form_data = {
            'job_number': request.form.get('job_number', '').strip(),
            'department': request.form.get('department', '').strip(),
            'work_type': request.form.get('work_type', '安裝').strip(),
            'line_count': request.form.get('line_count', '0').strip(),
            'remark': request.form.get('remark', '').strip(),
            'date': request.form.get('date', '').strip()
        }
        
        # 驗證必填字段
        if not form_data['job_number']:
            flash("工作單號不能為空", 'error')
            return redirect(url_for('index'))
        if not form_data['date']:
            flash("日期不能為空", 'error')
            return redirect(url_for('index'))
        
        # 處理產品數據
        products = {}
        product_prices = get_product_prices()
        for code in product_prices.keys():
            qty = request.form.get(f'product_{code}', '0').strip()
            if qty and int(qty) > 0:
                products[code] = int(qty)
        
        # 數據類型轉換
        form_data['line_count'] = int(form_data['line_count']) if form_data['line_count'] else 0
        
        # 添加記錄
        record_id = add_record(
            form_data['job_number'],
            form_data['department'],
            form_data['work_type'],
            form_data['line_count'],
            products,
            form_data['remark'],
            form_data['date']
        )
        
        if record_id:
            return redirect(url_for('view_records'))
        else:
            return redirect(url_for('index'))
            
    except Exception as e:
        flash(f"伺服器錯誤: {str(e)}", 'error')
        return redirect(url_for('index'))

# 其他路由...
# 這裡省略，實際應用中需要補充完整

if __name__ == '__main__':
    app.run(debug=True)