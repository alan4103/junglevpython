import os
from flask import Flask, render_template, request, redirect, url_for
from openpyxl import Workbook, load_workbook
from datetime import datetime

app = Flask(__name__)

# Excel 檔案路徑
EXCEL_FILE = 'work_records.xlsx'

# 初始化 Excel 檔案
def init_excel():
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.append(['工作單號', '日期', '線數', 'BW', '記錄時間'])
        wb.save(EXCEL_FILE)

# 獲取所有記錄
def get_all_records():
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    records = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0]:  # 確保工作單號不為空
            records.append({
                'job_number': row[0],
                'date': row[1],
                'line_count': row[2],
                'bw': row[3],
                'record_time': row[4]
            })
    return records

# 新增記錄
def add_record(job_number, date, line_count, bw):
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([
        job_number, 
        date, 
        line_count, 
        bw, 
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ])
    wb.save(EXCEL_FILE)

@app.route('/')
def index():
    init_excel()
    # 預設日期為今天
    default_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', default_date=default_date)

@app.route('/add', methods=['POST'])
def add():
    job_number = request.form.get('job_number')
    date = request.form.get('date')
    line_count = request.form.get('line_count')
    bw = request.form.get('bw')
    
    if job_number and date and line_count and bw:
        add_record(job_number, date, line_count, bw)
    return redirect(url_for('view_records'))

@app.route('/records')
def view_records():
    records = get_all_records()
    return render_template('records.html', records=records)

if __name__ == '__main__':
    app.run(debug=True)