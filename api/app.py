import json
import os
import secrets
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = '/tmp/users.json'
KEYS_FILE = '/tmp/keys.json'
MASTER_USERNAME = "MASTER"
MASTER_PASSWORD = "RAGNAR-TOP1"  # كلمة سر الماستر

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    key = data.get('key')
    
    users = load_data()
    keys = load_keys()
    
    if username in users:
        return jsonify({'success': False, 'error': 'الاسم موجود'})
    if key not in keys or keys[key] is True:
        return jsonify({'success': False, 'error': 'مفتاح غير صالح أو مستخدم'})
    
    # تسجيل المستخدم
    users[username] = {
        'password': password,
        'token': '',
        'admin_password': 'X1R_RAGNAR',
        'max_users': 100,
        'active_users': [],
        'is_active': False
    }
    save_data(users)
    # استهلاك المفتاح
    keys[key] = False  # تم استخدامه
    save_keys(keys)
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username == MASTER_USERNAME and password == MASTER_PASSWORD:
        return jsonify({'success': True, 'is_master': True})
    
    users = load_data()
    if username in users and users[username]['password'] == password:
        return jsonify({'success': True, 'is_master': False})
    return jsonify({'success': False, 'error': 'بيانات خاطئة'})

@app.route('/api/get-user-data', methods=['POST'])
def get_user_data():
    data = request.json
    username = data.get('username')
    users = load_data()
    if username in users:
        u = users[username]
        return jsonify({
            'token': u['token'],
            'admin_password': u['admin_password'],
            'max_users': u['max_users'],
            'active_users': len(u['active_users']),
            'is_active': u['is_active']
        })
    return jsonify({'error': 'User not found'})

@app.route('/api/update-user-bot', methods=['POST'])
def update_user_bot():
    data = request.json
    username = data.get('username')
    users = load_data()
    if username in users:
        users[username]['token'] = data.get('token', '')
        users[username]['admin_password'] = data.get('admin_password', '')
        users[username]['max_users'] = data.get('max_users', 100)
        save_data(users)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/toggle-user-bot', methods=['POST'])
def toggle_user_bot():
    data = request.json
    username = data.get('username')
    users = load_data()
    if username in users:
        users[username]['is_active'] = not users[username]['is_active']
        save_data(users)
        return jsonify({'success': True, 'is_active': users[username]['is_active']})
    return jsonify({'success': False})

@app.route('/api/master-data', methods=['POST'])
def master_data():
    users = load_data()
    result = []
    for u, d in users.items():
        result.append({
            'username': u,
            'token': d['token'],
            'max_users': d['max_users'],
            'active_users': len(d['active_users']),
            'is_active': d['is_active']
        })
    return jsonify({'users': result})

@app.route('/api/generate-key', methods=['POST'])
def generate_key():
    # هذه الوظيفة لا تحتاج كلمة سر لأنها محمية بـ Master Panel من الواجهة
    keys = load_keys()
    new_key = secrets.token_hex(8)
    keys[new_key] = True  # غير مستخدم
    save_keys(keys)
    return jsonify({'key': new_key})

if __name__ == '__main__':
    app.run(debug=True)
