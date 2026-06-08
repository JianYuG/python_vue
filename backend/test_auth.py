import urllib.request
import json

base_url = 'http://localhost:8090/api/auth'

def post(path, data):
    req = urllib.request.Request(
        f'{base_url}{path}',
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'}
    )
    try:
        r = urllib.request.urlopen(req)
        return r.read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()}"

def get(path, token):
    req = urllib.request.Request(
        f'{base_url}{path}',
        headers={'Authorization': f'Bearer {token}'}
    )
    try:
        r = urllib.request.urlopen(req)
        return r.read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()}"

# 1. 注册 - 密码 "test123" 的 SHA-256 = 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
print("=== 注册 ===")
reg_res = post('/register', {
    "username": "testuser",
    "password": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    "nickname": "测试用户"
})
print(reg_res)

# 2. 登录
print("\n=== 登录 ===")
login_res = post('/login', {
    "username": "testuser",
    "password": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
})
print(login_res)

# 提取 token
try:
    token = json.loads(login_res)['data']['token']
except:
    print("登录失败，无法获取 token")
    token = None

# 3. 获取用户信息
if token:
    print("\n=== 用户信息 ===")
    info_res = get('/user-info', token)
    print(info_res)
