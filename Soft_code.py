'''
Colabratoryにて実行

始めにインストール　↓

!pip install flask flask-ngrok
!pip install pyngrok

'''


import os
from pyngrok import ngrok
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # アップロードファイルの保存先
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ngrokの設定
ngrok.set_auth_token("2jP6Q9DbGiw62RYhnGB2fhWkdHR_7Vt82jU26MDucF1kThZEL")
public_url = ngrok.connect(5000)
print(" * ngrok URL:", public_url)

# 初期データ
subjects = {}
notes = {}
ratings = {}
files = {}
due_dates = {i: datetime(2024, 7, 1) for i in range(1, 16)}  # サンプルの期限日

# HTMLテンプレート
template = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>課題提出状況管理アプリ</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1, h2 {
            color: #333;
        }
        form {
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        th {
            background-color: #f4f4f4;
        }
        select, button {
            padding: 5px;
            margin-right: 5px;
        }
        .unsubmitted {
            background-color: blue;
            color: white;
        }
        .submitted {
            background-color: yellow;
        }
        .late {
            background-color: red;
            color: white;
        }
        .expired {
            background-color: gray;
            color: white;
        }
        .memo {
            background-color: lightgreen;
            color: black;
        }
        .no-memo {
            background-color: lightgray;
            color: black;
        }
        .toc {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fff;
            border: 1px solid #ccc;
            padding: 10px;
            max-width: 200px;
        }
        .toc a {
            text-decoration: none;
            color: #333;
        }
        .memo-section {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 70%;
            height: 70%;
            background-color: #f9f9f9;
            padding: 20px;
            border: 1px solid #ccc;
            z-index: 1000;
            overflow: auto;
        }
        .rating-section {
            margin-bottom: 20px;
        }
        .rating-input {
            width: 100px;
            text-align: right;
        }
        .score {
            font-weight: bold;
        }
        @media (max-width: 600px) {
            th, td {
                font-size: 12px;
                padding: 5px;
            }
            select, button {
                width: 100%;
                margin-bottom: 5px;
            }
            .toc {
                position: static;
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    <h1>課題提出状況管理アプリ</h1>
    <form method="POST" action="/add_subject">
        <label for="subject_name">授業科目名:</label>
        <input type="text" id="subject_name" name="subject_name" required>
        <button type="submit">追加</button>
    </form>
    <div class="toc">
        <h3>目次</h3>
        <ul>
            {% for subject in subjects.keys() %}
                <li><a href="#{{ subject }}">{{ subject }}</a></li>
            {% endfor %}
        </ul>
    </div>
    <hr>
    {% for subject, tasks in subjects.items() %}
        <h2 id="{{ subject }}">{{ subject }}</h2>
        <div class="rating-section">
            <form method="POST" action="/update_rating/{{ subject }}" style="display: inline;">
                <label for="rating">評定率:</label>
                <input type="number" id="rating" name="rating" class="rating-input" min="0" max="100" value="{{ ratings.get(subject, 100) }}">%
                <button type="submit">更新</button>
            </form>
        </div>
        <table>
            <tr>
                <th>講義回</th>
                <th>状況</th>
                <th>操作</th>
                <th>メモ</th>
                <th>提出ファイル</th>
            </tr>
            {% for i in range(1, 16) %}
            {% set status = tasks.get(i, '未提出') %}
            {% set class_name = 'unsubmitted' if status == '未提出' else 'submitted' if status == '提出済み' else 'late' if status == '遅れて提出' else 'expired' %}
            <tr>
                <td>{{ i }}</td>
                <td class="{{ class_name }}" id="status-{{ subject }}-{{ i }}">{{ status }}</td>
                <td>
                    <select name="status" onchange="updateStatus('{{ subject }}', {{ i }}, this)">
                        <option value="未提出" {% if status == '未提出' %}selected{% endif %}>未提出</option>
                        <option value="提出済み" {% if status == '提出済み' %}selected{% endif %}>提出済み</option>
                        <option value="遅れて提出" {% if status == '遅れて提出' %}selected{% endif %}>遅れて提出</option>
                        <option value="期限切れ" {% if status == '期限切れ' %}selected{% endif %}>期限切れ</option>
                    </select>
                </td>
                <td>
                    <button onclick="toggleMemo('{{ subject }}', {{ i }})" class="{{ 'memo' if notes.get(subject, {}).get(i) else 'no-memo' }}">メモ</button>
                </td>
                <td>
                    <form method="POST" action="/upload_file/{{ subject }}/{{ i }}" enctype="multipart/form-data" style="display: inline;">
                        <input type="file" name="file">
                        <button type="submit">アップロード</button>
                    </form>
                    <ul>
                        {% for filename in files.get(subject, {}).get(i, []) %}
                            <li><a href="/download_file/{{ subject }}/{{ i }}/{{ filename }}">{{ filename }}</a></li>
                        {% endfor %}
                    </ul>
                </td>
            </tr>
            {% endfor %}
        </table>
        {% for i in range(1, 16) %}
        <div id="memo-section-{{ subject }}-{{ i }}" class="memo-section">
            <form method="POST" action="/save_note/{{ subject }}/{{ i }}">
                <textarea name="note" rows="20" cols="80">{{ notes.get(subject, {}).get(i, '') }}</textarea>
                <br>
                <button type="submit">保存</button>
            </form>
            <button onclick="hideMemo()">閉じる</button>
        </div>
        {% endfor %}
        <p class="score">最終点数: {{ calculate_score(subjects[subject], ratings.get(subject, 100)) }}</p>
        <hr>
    {% endfor %}
    <script>
        function updateStatus(subject, index, selectElement) {
            var status = selectElement.value;
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/update_status/" + subject + "/" + index, true);
            xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 300) {
                    var response = xhr.responseText;
                    document.getElementById('status-' + subject + '-' + index).className = getStatusClass(status);
                    document.getElementById('status-' + subject + '-' + index).textContent = status;
                }
            };
            xhr.send("status=" + encodeURIComponent(status));
        }

        function getStatusClass(status) {
            if (status === "未提出") return "unsubmitted";
            if (status === "提出済み") return "submitted";
            if (status === "遅れて提出") return "late";
            if (status === "期限切れ") return "expired";
            return "";
        }

        function toggleMemo(subject, index) {
            var memoSection = document.getElementById('memo-section-' + subject + '-' + index);
            if (memoSection.style.display === "block") {
                memoSection.style.display = "none";
            } else {
                memoSection.style.display = "block";
            }
        }

        function hideMemo() {
            var memoSections = document.querySelectorAll('.memo-section');
            memoSections.forEach(function(section) {
                section.style.display = 'none';
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(template, subjects=subjects, notes=notes, ratings=ratings, files=files, calculate_score=calculate_score)

@app.route('/add_subject', methods=['POST'])
def add_subject():
    subject_name = request.form['subject_name']
    if subject_name not in subjects:
        subjects[subject_name] = {}
        notes[subject_name] = {}
        files[subject_name] = {}
    return render_template_string(template, subjects=subjects, notes=notes, ratings=ratings, files=files, calculate_score=calculate_score)

@app.route('/update_status/<subject>/<int:task_id>', methods=['POST'])
def update_status(subject, task_id):
    status = request.form['status']
    if subject in subjects:
        subjects[subject][task_id] = status
    return render_template_string(template, subjects=subjects, notes=notes, ratings=ratings, files=files, calculate_score=calculate_score)

@app.route('/save_note/<subject>/<int:task_id>', methods=['POST'])
def save_note(subject, task_id):
    note = request.form['note']
    if subject in notes:
        notes[subject][task_id] = note
    else:
        notes[subject] = {task_id: note}
    return render_template_string(template, subjects=subjects, notes=notes, ratings=ratings, files=files, calculate_score=calculate_score)

@app.route('/update_rating/<subject>', methods=['POST'])
def update_rating(subject):
    rating = request.form['rating']
    if subject in subjects:
        try:
            rating = float(rating)
            ratings[subject] = rating
        except ValueError:
            pass
    return render_template_string(template, subjects=subjects, notes=notes, ratings=ratings, files=files, calculate_score=calculate_score)

@app.route('/upload_file/<subject>/<int:task_id>', methods=['POST'])
def upload_file(subject, task_id):
    if subject not in files:
        files[subject] = {}
    if task_id not in files[subject]:
        files[subject][task_id] = []

    if 'file' in request.files:
        file = request.files['file']
        if file.filename:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            files[subject][task_id].append(filename)

    return render_template_string(template, subjects=subjects, notes=notes, ratings=ratings, files=files, calculate_score=calculate_score)

@app.route('/download_file/<subject>/<int:task_id>/<filename>', methods=['GET'])
def download_file(subject, task_id, filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def calculate_score(tasks, rating):
    total_score = 0
    count = 0
    for i in range(1, 16):
        status = tasks.get(i, '未提出')
        if status == '提出済み':
            score = 100
        elif status == '遅れて提出':
            score = 60
        else:
            score = 0
        total_score += score
        count += 1
    average_score = total_score / count if count > 0 else 0
    final_score = average_score * (rating / 100)
    return final_score

if __name__ == '__main__':
    app.run()
