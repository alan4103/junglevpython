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
        ws.append(['ID', '工作單號', '部門', '線數', '備註', '記錄時間', '日期'])
        wb.save(EXCEL_FILE)

# 獲取所有記錄
def get_all_records():
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    records = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[1]:  # 確保工作單號不為空
            records.append({
                'id': row[0],
                'job_number': row[1],
                'department': row[2],
                'line_count': row[3],
                'remark': row[4],
                'record_time': row[5],
                'date': row[6]
            })
    return records

# 搜尋記錄
def search_records(keyword):
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    records = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[1] and (keyword.lower() in str(row[1]).lower() or  # 工作單號
                       keyword.lower() in str(row[2]).lower() or  # 部門
                       keyword.lower() in str(row[4]).lower()):   # 備註
            records.append({
                'id': row[0],
                'job_number': row[1],
                'department': row[2],
                'line_count': row[3],
                'remark': row[4],
                'record_time': row[5],
                'date': row[6]
            })
    return records

# 新增記錄
def add_record(job_number, department, line_count, remark, date):
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    
    # 生成唯一ID (當前最大ID + 1)
    max_id = 0
    for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
        if row[0] and isinstance(row[0], int):
            max_id = max(max_id, row[0])
    
    ws.append([
        max_id + 1,
        job_number,
        department,
        line_count,
        remark,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        date
    ])
    wb.save(EXCEL_FILE)

# 更新記錄
def update_record(record_id, job_number, department, line_count, remark, date):
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    
    for row in ws.iter_rows(min_row=2):
        if row[0].value == record_id:
            row[1].value = job_number
            row[2].value = department
            row[3].value = line_count
            row[4].value = remark
            row[6].value = date
            break
    
    wb.save(EXCEL_FILE)

# 刪除記錄
def delete_record(record_id):
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    
    # 找到要刪除的行
    row_to_delete = None
    for idx, row in enumerate(ws.iter_rows(min_row=2, max_col=1), start=2):
        if row[0].value == record_id:
            row_to_delete = idx
            break
    
    if row_to_delete:
        ws.delete_rows(row_to_delete)
        wb.save(EXCEL_FILE)
        return True
    return False

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
    remark = request.form.get('remark')
    date = request.form.get('date')
    
    if job_number and date:
        add_record(job_number, department, line_count, remark, date)
    return redirect(url_for('view_records'))

@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit(record_id):
    if request.method == 'POST':
        job_number = request.form.get('job_number')
        department = request.form.get('department')
        line_count = request.form.get('line_count')
        remark = request.form.get('remark')
        date = request.form.get('date')
        
        update_record(record_id, job_number, department, line_count, remark, date)
        return redirect(url_for('view_records'))
    
    # GET 請求時顯示編輯表單
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    record = None
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] == record_id:
            record = {
                'id': row[0],
                'job_number': row[1],
                'department': row[2],
                'line_count': row[3],
                'remark': row[4],
                'date': row[6]
            }
            break
    
    if not record:
        return redirect(url_for('view_records'))
    
    return render_template('edit.html', record=record)

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
    app.run(debug=True)