import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')  # 從環境變量獲取

# 配置
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)
EXCEL_FILE = os.path.join(DATA_DIR, 'work_records.xlsx')

# 代號價格對照表
CODE_PRICES = {
    "007": 18,
    "008": 25,
    "009": 30,
    "010": 15,
    "011": 20
}

def init_excel_file():
    """初始化Excel文件"""
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=[
            '工作單號', '工作日期', '代號', 
            '單價', '數量', '總價', 
            '工作內容', '記錄時間'
        ])
        df.to_excel(EXCEL_FILE, index=False)

@app.route('/')
def index():
    """主頁面"""
    init_excel_file()
    records = pd.read_excel(EXCEL_FILE).to_dict('records')
    return render_template('index.html', 
                         codes=CODE_PRICES.keys(),
                         records=records)

@app.route('/add_record', methods=['POST'])
def add_record():
    """添加新記錄"""
    try:
        # 獲取表單數據
        work_id = request.form.get('work_id')
        work_date = request.form.get('work_date')
        code = request.form.get('code')
        quantity = int(request.form.get('quantity', 1))
        content = request.form.get('content')
        
        # 驗證數據
        if not all([work_id, work_date, code]):
            flash('請填寫所有必填字段', 'error')
            return redirect(url_for('index'))
        
        # 計算價格
        price = CODE_PRICES.get(code, 0)
        total = price * quantity
        
        # 創建新記錄
        new_record = {
            '工作單號': work_id,
            '工作日期': work_date,
            '代號': code,
            '單價': price,
            '數量': quantity,
            '總價': total,
            '工作內容': content,
            '記錄時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 保存到Excel
        df = pd.read_excel(EXCEL_FILE)
        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)
        
        flash('記錄已成功添加', 'success')
    except Exception as e:
        flash(f'添加記錄時出錯: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/export')
def export_records():
    """導出Excel文件"""
    return send_file(
        EXCEL_FILE,
        as_attachment=True,
        download_name='work_records_export.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    init_excel_file()
    # Heroku 會設置 PORT 環境變量
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)