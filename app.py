import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from openpyxl import Workbook, load_workbook
from datetime import datetime
from io import BytesIO

app = Flask(__name__)

# Excel 檔案路徑
EXCEL_FILE = 'work_records.xlsx'

# 初始化 Excel 檔案
def init_excel():
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.append(['工作單號', '部門', '線數', 'BW (可含數學符號)', '備註', '記錄時間', '日期'])
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
                'department': row[1],
                'line_count': row[2],
                'bw': row[3],
                'remark': row[4],
                'record_time': row[5],
                'date': row[6]
            })
    return records

# 新增記錄
def add_record(job_number, department, line_count, bw, remark, date):
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([
        job_number,
        department,
        line_count,
        bw,
        remark,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        date
    ])
    wb.save(EXCEL_FILE)

# 下載 Excel 文件
@app.route('/download')
def download_excel():
    init_excel()
    file_stream = BytesIO()
    wb = load_workbook(EXCEL_FILE)
    wb.save(file_stream)
    file_stream.seek(0)
    return send_file(
        file_stream,
        as_attachment=True,
        download_name='work_records.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/')
def index():
    init_excel()
    default_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', default_date=default_date)

@app.route('/add', methods=['POST'])
def add():
    job_number = request.form.get('job_number')
    department = request.form.get('department')
    line_count = request.form.get('line_count')
    bw = request.form.get('bw')
    remark = request.form.get('remark')
    date = request.form.get('date')
    
    if job_number and date:
        add_record(job_number, department, line_count, bw, remark, date)
    return redirect(url_for('view_records'))

@app.route('/records')
def view_records():
    records = get_all_records()
    return render_template('records.html', records=records)

if __name__ == '__main__':
    app.run(debug=True)