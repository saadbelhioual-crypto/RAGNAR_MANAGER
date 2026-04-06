import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = '/tmp/users.json'
KEYS_FILE = '/tmp/keys.json'
MASTER_USERNAME = "MASTER"
MASTER_PASSWORD = "RAGNAR-TOP1"
BOT_RUNNER_KEY = "RAGNAR-BOT-RUNNER-KEY-2025"

# إنشاء 20 مفتاح مبدئي
def init_keys():
    if not os.path.exists(KEYS_FILE):
        keys = {f"KEY-{i+1}": True for i in range(20)}  # 20 مفتاح
        with open(KEYS_FILE, 'w') as f:
            json.dump(keys, f)
    return load_keys()

def load_keys():
    with open(KEYS_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f)

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f)

init_keys()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    key = data.get('key')
    
    users = load_users()
    keys = load_keys()
    
    if username in users:
        return jsonify({'success': False, 'error': 'الاسم موجود بالفعل'})
    
    if key not in keys or keys[key] is False:
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
    save_users(users)
    
    # استهلاك المفتاح
    keys[key] = False
    save_keys(keys)
    
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username == MASTER_USERNAME and password == MASTER_PASSWORD:
        keys = load_keys()
        available_keys = [k for k, v in keys.items() if v]
        return jsonify({
            'success': True, 
            'is_master': True,
            'available_keys': len(available_keys),
            'total_keys': len(keys)
        })
    
    users = load_users()
    if username in users and users[username]['password'] == password:
        return jsonify({'success': True, 'is_master': False})
    
    return jsonify({'success': False, 'error': 'بيانات خاطئة'})

@app.route('/api/get-keys', methods=['POST'])
def get_keys():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username != MASTER_USERNAME or password != MASTER_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    
    keys = load_keys()
    available = [k for k, v in keys.items() if v]
    used = [k for k, v in keys.items() if not v]
    
    return jsonify({
        'available_keys': available,
        'used_keys': used,
        'available_count': len(available),
        'used_count': len(used),
        'total': len(keys)
    })

@app.route('/api/get-user-data', methods=['POST'])
def get_user_data():
    data = request.json
    username = data.get('username')
    users = load_users()
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
    users = load_users()
    if username in users:
        users[username]['token'] = data.get('token', '')
        users[username]['admin_password'] = data.get('admin_password', '')
        users[username]['max_users'] = data.get('max_users', 100)
        save_users(users)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/toggle-user-bot', methods=['POST'])
def toggle_user_bot():
    data = request.json
    username = data.get('username')
    users = load_users()
    if username in users:
        users[username]['is_active'] = not users[username]['is_active']
        save_users(users)
        return jsonify({'success': True, 'is_active': users[username]['is_active']})
    return jsonify({'success': False})

@app.route('/api/bot-runner-data', methods=['POST'])
def bot_runner_data():
    data = request.json
    key = data.get('key')
    
    if key != BOT_RUNNER_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    users = load_users()
    result = []
    for u, d in users.items():
        result.append({
            'username': u,
            'token': d['token'],
            'admin_password': d['admin_password'],
            'max_users': d['max_users'],
            'active_users': d['active_users'],
            'is_active': d['is_active']
        })
    return jsonify({'users': result})

@app.route('/api/update-user-active', methods=['POST'])
def update_user_active():
    data = request.json
    key = data.get('key')
    username = data.get('username')
    active_users = data.get('active_users', [])
    
    if key != BOT_RUNNER_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    users = load_users()
    if username in users:
        users[username]['active_users'] = active_users
        save_users(users)
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True)
