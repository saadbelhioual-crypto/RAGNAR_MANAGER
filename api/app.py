import json
import os
import secrets
import datetime
from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS
import re

app = Flask(__name__)
app.secret_key = 'RAGNAR-SECRET-KEY-2025'
CORS(app)

DATA_FILE = '/tmp/users.json'
KEYS_FILE = '/tmp/keys.json'
MESSAGES_FILE = '/tmp/messages.json'
OWNER_FILE = '/tmp/owner.json'
DEFAULT_SETTINGS_FILE = '/tmp/default_settings.json'

# ========== بيانات المالك ==========
MASTER_USERNAME = "RAGNAR"
MASTER_PASSWORD = "RAGNAR-WEB1"
MASTER_EXPIRY = (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat()

# ========== المفتاح المجاني (مرة واحدة فقط) ==========
FREE_KEY = "FREE-KEY"
FREE_KEY_EXPIRY = (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()

# ========== المفتاح الخاص بالبوت الخارجي ==========
BOT_RUNNER_KEY = "RAGNAR-BOT-RUNNER-KEY-2025"

# ========== الإعدادات الافتراضية (يغيرها المالك) ==========
def load_default_settings():
    if os.path.exists(DEFAULT_SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {
        'token': '',
        'admin_password': 'X1R_RAGNAR',
        'max_users': 100,
        'is_active': False
    }

def save_default_settings(settings):
    with open(DEFAULT_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

# ========== قائمة البوتات المحظورة ==========
BLOCKED_AGENTS = [
    'python-requests', 'python-telegram-bot', 'TelegramBot',
    'WebsiteDownloader', 'wget', 'curl', 'httpx',
    'scrapy', 'beautifulsoup', 'selenium', 'phantomjs',
    'bot', 'spider', 'crawler', 'scraper', 'download'
]

BLOCKED_IPS = []

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
    keys = {
        FREE_KEY: {'used': False, 'expiry_date': FREE_KEY_EXPIRY}
    }
    for i in range(1, 50):
        keys[f'KEY-{secrets.token_hex(3).upper()}'] = {'used': False, 'expiry_date': None}
    save_keys(keys)
    return keys

def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f)

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return {
        'welcome_message': '👋 مرحباً بك في بوت RAGNAR x STRAVEX!\nاستخدم /help لمعرفة الأوامر',
        'help_message': '📋 الأوامر المتاحة:\n/info <id> - معلومات لاعب\n/stats - إحصائيات\n/help - المساعدة'
    }

def save_messages(messages):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f)

def load_owner_info():
    if os.path.exists(OWNER_FILE):
        with open(OWNER_FILE, 'r') as f:
            return json.load(f)
    return {
        'owner_id': '8213029377',
        'owner_bot_name': '@X1R_RAGNAR',
        'owner_expiry': MASTER_EXPIRY
    }

def save_owner_info(info):
    with open(OWNER_FILE, 'w') as f:
        json.dump(info, f)

@app.before_request
def block_malicious_bots():
    user_agent = request.headers.get('User-Agent', '')
    ip = request.remote_addr
    
    if request.path == '/api/bot-runner-data':
        data = request.get_json(silent=True)
        if data and data.get('key') == BOT_RUNNER_KEY:
            return None
    
    if request.path == '/api/update-user-active':
        data = request.get_json(silent=True)
        if data and data.get('key') == BOT_RUNNER_KEY:
            return None
    
    if ip in BLOCKED_IPS:
        return make_response("⛔ Access Denied", 403)
    
    for agent in BLOCKED_AGENTS:
        if agent.lower() in user_agent.lower():
            return make_response("⛔ Access Denied - Bot detected", 403)
    
    if not user_agent or len(user_agent) < 5:
        return make_response("⛔ Invalid Request", 403)
    
    if not request.path.startswith('/api/'):
        allowed_browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera', 'Mobile']
        is_browser = any(b in user_agent for b in allowed_browsers)
        if not is_browser and not user_agent.startswith('Mozilla'):
            return make_response("⛔ Access Denied", 403)
    
    return None

@app.after_request
def add_security_headers(response):
    response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response

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
    
    # جلب الإعدادات الافتراضية من المالك
    default_settings = load_default_settings()
    
    users[username] = {
        'password': password,
        'token': default_settings.get('token', ''),
        'admin_password': default_settings.get('admin_password', 'X1R_RAGNAR'),
        'max_users': default_settings.get('max_users', 100),
        'active_users': [],
        'is_active': default_settings.get('is_active', False),
        'expiry_date': expiry_date,
        'created_at': datetime.datetime.now().isoformat()
    }
    save_users(users)
    
    # استهلاك المفتاح (مرة واحدة فقط)
    keys[key]['used'] = True
    save_keys(keys)
    
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    owner_info = load_owner_info()
    
    if username == MASTER_USERNAME and password == MASTER_PASSWORD:
        session['user'] = username
        session['is_master'] = True
        keys = load_keys()
        available_keys = [k for k, v in keys.items() if not v.get('used', False) and k != FREE_KEY]
        default_settings = load_default_settings()
        return jsonify({
            'success': True, 
            'is_master': True,
            'available_keys': len(available_keys),
            'total_keys': len([k for k in keys if k != FREE_KEY]),
            'owner_expiry': owner_info.get('owner_expiry', MASTER_EXPIRY),
            'default_settings': default_settings
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
        if k == FREE_KEY:
            continue
        is_used = v.get('used', False)
        if not is_used:
            available_count += 1
        result.append({
            'key': k,
            'used': is_used,
            'expiry_date': v.get('expiry_date')
        })
    return jsonify({'keys': result, 'available_count': available_count, 'total': len([k for k in keys if k != FREE_KEY])})

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
    
    if key == FREE_KEY:
        return jsonify({'success': False, 'error': 'لا يمكن حذف المفتاح المجاني'})
    
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

@app.route('/api/update-owner-info', methods=['POST'])
def update_owner_info():
    if not session.get('is_master'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    owner_info = load_owner_info()
    owner_info['owner_id'] = data.get('owner_id', owner_info.get('owner_id'))
    owner_info['owner_bot_name'] = data.get('owner_bot_name', owner_info.get('owner_bot_name'))
    save_owner_info(owner_info)
    return jsonify({'success': True})

@app.route('/api/get-owner-info', methods=['POST'])
def get_owner_info():
    owner_info = load_owner_info()
    messages = load_messages()
    default_settings = load_default_settings()
    return jsonify({
        'owner_id': owner_info.get('owner_id'),
        'owner_bot_name': owner_info.get('owner_bot_name'),
        'owner_expiry': owner_info.get('owner_expiry'),
        'welcome_message': messages.get('welcome_message'),
        'help_message': messages.get('help_message'),
        'default_settings': default_settings
    })

@app.route('/api/update-messages', methods=['POST'])
def update_messages():
    if not session.get('is_master'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    messages = load_messages()
    if 'welcome_message' in data:
        messages['welcome_message'] = data['welcome_message']
    if 'help_message' in data:
        messages['help_message'] = data['help_message']
    save_messages(messages)
    return jsonify({'success': True})

@app.route('/api/update-default-settings', methods=['POST'])
def update_default_settings():
    """تحديث الإعدادات الافتراضية (يغيرها المالك وتتغير عند جميع المستخدمين)"""
    if not session.get('is_master'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    default_settings = load_default_settings()
    
    if 'token' in data:
        default_settings['token'] = data['token']
    if 'admin_password' in data:
        default_settings['admin_password'] = data['admin_password']
    if 'max_users' in data:
        default_settings['max_users'] = data['max_users']
    if 'is_active' in data:
        default_settings['is_active'] = data['is_active']
    
    save_default_settings(default_settings)
    
    # تحديث جميع المستخدمين بالإعدادات الجديدة
    users = load_users()
    changed = False
    for username, user_data in users.items():
        if 'token' in data and user_data.get('token') != default_settings['token']:
            user_data['token'] = default_settings['token']
            changed = True
        if 'admin_password' in data and user_data.get('admin_password') != default_settings['admin_password']:
            user_data['admin_password'] = default_settings['admin_password']
            changed = True
        if 'max_users' in data and user_data.get('max_users') != default_settings['max_users']:
            user_data['max_users'] = default_settings['max_users']
            changed = True
        if 'is_active' in data and user_data.get('is_active') != default_settings['is_active']:
            user_data['is_active'] = default_settings['is_active']
            changed = True
    
    if changed:
        save_users(users)
    
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
    """تحديث إعدادات المستخدم الفردي (لا تؤثر على الآخرين)"""
    data = request.json
    username = data.get('username')
    users = load_users()
    if username in users:
        users[username]['token'] = data.get('token', users[username]['token'])
        users[username]['admin_password'] = data.get('admin_password', users[username]['admin_password'])
        users[username]['max_users'] = data.get('max_users', users[username]['max_users'])
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
