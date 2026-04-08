import json
import os
import secrets
import datetime
from flask import Flask, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'RAGNAR-SECRET-KEY-2025'
CORS(app)

DATA_FILE = '/tmp/users.json'
KEYS_FILE = '/tmp/keys.json'

# ========== بيانات المالك الجديدة ==========
MASTER_USERNAME = "RAGNAR"
MASTER_PASSWORD = "RAGNAR-WEB1"
# ===========================================

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f)

def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r') as f:
            return json.load(f)
    keys = {}
    for i in range(1, 51):
        keys[f'KEY-{secrets.token_hex(3).upper()}'] = {'used': False, 'expiry_date': None}
    save_keys(keys)
    return keys

def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    key = data.get('key')
    
    users = load_users()
    keys = load_keys()
    
    if username in users:
        return jsonify({'success': False, 'error': 'الاسم موجود'})
    
    if key not in keys:
        return jsonify({'success': False, 'error': 'مفتاح غير صالح'})
    
    if keys[key].get('used', False):
        return jsonify({'success': False, 'error': 'المفتاح مستخدم بالفعل'})
    
    expiry_date = keys[key].get('expiry_date')
    if expiry_date:
        expiry = datetime.datetime.fromisoformat(expiry_date)
        if datetime.datetime.now() > expiry:
            return jsonify({'success': False, 'error': 'المفتاح منتهي الصلاحية'})
    
    users[username] = {
        'password': password,
        'token': '',
        'admin_password': 'X1R_RAGNAR',
        'max_users': 100,
        'active_users': [],
        'is_active': False,
        'expiry_date': expiry_date,
        'created_at': datetime.datetime.now().isoformat()
    }
    save_users(users)
    
    # ✅ حذف المفتاح بالكامل بعد استخدامه (وليس مجرد تعليمه كمستخدم)
    del keys[key]
    save_keys(keys)
    
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # ✅ بيانات المالك الجديدة
    if username == MASTER_USERNAME and password == MASTER_PASSWORD:
        session['user'] = username
        session['is_master'] = True
        keys = load_keys()
        available_keys = [k for k, v in keys.items() if not v.get('used', False)]
        return jsonify({
            'success': True, 
            'is_master': True,
            'available_keys': len(available_keys),
            'total_keys': len(keys)
        })
    
    users = load_users()
    if username in users and users[username]['password'] == password:
        expiry_date = users[username].get('expiry_date')
        if expiry_date:
            expiry = datetime.datetime.fromisoformat(expiry_date)
            if datetime.datetime.now() > expiry:
                return jsonify({'success': False, 'error': 'انتهت صلاحية حسابك'})
        session['user'] = username
        session['is_master'] = False
        return jsonify({'success': True, 'is_master': False})
    
    return jsonify({'success': False, 'error': 'بيانات خاطئة'})

@app.route('/api/get-all-keys', methods=['POST'])
def get_all_keys():
    if not session.get('is_master'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    keys = load_keys()
    result = []
    available_count = 0
    for k, v in keys.items():
        is_used = v.get('used', False)
        if not is_used:
            available_count += 1
        result.append({
            'key': k,
            'used': is_used,
            'expiry_date': v.get('expiry_date')
        })
    return jsonify({'keys': result, 'available_count': available_count, 'total': len(keys)})

@app.route('/api/generate-key', methods=['POST'])
def generate_key():
    if not session.get('is_master'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    new_key = data.get('key')
    expiry_days = data.get('expiry_days', 7)
    
    keys = load_keys()
    if new_key in keys:
        return jsonify({'success': False, 'error': 'المفتاح موجود'})
    
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=expiry_days)).isoformat()
    keys[new_key] = {'used': False, 'expiry_date': expiry_date}
    save_keys(keys)
    return jsonify({'success': True})

@app.route('/api/delete-key', methods=['POST'])
def delete_key():
    if not session.get('is_master'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    key = data.get('key')
    
    keys = load_keys()
    if key not in keys:
        return jsonify({'success': False, 'error': 'مفتاح غير موجود'})
    
    del keys[key]
    save_keys(keys)
    return jsonify({'success': True})

@app.route('/api/change-master-password', methods=['POST'])
def change_master_password():
    if not session.get('is_master'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    global MASTER_PASSWORD
    data = request.json
    new_password = data.get('new_password')
    
    MASTER_PASSWORD = new_password
    return jsonify({'success': True})

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
            'is_active': u['is_active'],
            'expiry_date': u.get('expiry_date')
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
    
    if key != "RAGNAR-BOT-RUNNER-KEY-2025":
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
            'is_active': d['is_active'],
            'expiry_date': d.get('expiry_date')
        })
    return jsonify({'users': result})

@app.route('/api/update-user-active', methods=['POST'])
def update_user_active():
    data = request.json
    key = data.get('key')
    username = data.get('username')
    active_users = data.get('active_users', [])
    
    if key != "RAGNAR-BOT-RUNNER-KEY-2025":
        return jsonify({'error': 'Unauthorized'}), 401
    
    users = load_users()
    if username in users:
        users[username]['active_users'] = active_users
        save_users(users)
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True)
