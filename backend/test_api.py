"""Quick API smoke test for all rev_2 endpoints."""
import requests

BASE = 'http://127.0.0.1:8000'

# Login as owner
r = requests.post(f'{BASE}/api/auth/login/', json={'username': 'owner', 'password': 'admin123'})
assert r.status_code == 200, f'Login failed: {r.status_code}'
token = r.json()['access']
h = {'Authorization': f'Bearer {token}'}
print(f'LOGIN: 200 OK (role={r.json()["user"]["role"]}, tier={r.json()["user"]["tier"]})')

# Test all endpoints
endpoints = [
    ('GET', '/api/auth/me/', h, 'ME'),
    ('GET', '/api/tenant/', None, 'TENANT (public)'),
    ('GET', '/api/bookings/services/', None, 'SERVICES (public)'),
    ('GET', '/api/bookings/', h, 'BOOKINGS'),
    ('GET', '/api/bookings/slots/', None, 'SLOTS (public)'),
    ('GET', '/api/staff/', h, 'STAFF'),
    ('GET', '/api/staff/shifts/', h, 'SHIFTS'),
    ('GET', '/api/staff/leave/', h, 'LEAVE'),
    ('GET', '/api/staff/training/', h, 'TRAINING'),
    ('GET', '/api/comms/channels/', h, 'CHANNELS'),
    ('GET', '/api/compliance/incidents/', h, 'INCIDENTS'),
    ('GET', '/api/compliance/rams/', h, 'RAMS'),
    ('GET', '/api/documents/', h, 'DOCUMENTS'),
    ('GET', '/api/crm/leads/', h, 'CRM LEADS'),
    ('GET', '/api/audit/', h, 'AUDIT LOG'),
    ('GET', '/api/analytics/dashboard/', h, 'ANALYTICS'),
]

passed = 0
failed = 0
for method, path, headers, name in endpoints:
    r = requests.request(method, f'{BASE}{path}', headers=headers)
    status = r.status_code
    if status == 200:
        data = r.json()
        count = len(data) if isinstance(data, list) else 'obj'
        print(f'  {name}: {status} OK ({count})')
        passed += 1
    else:
        print(f'  {name}: {status} FAIL')
        failed += 1

# Test RBAC - staff should NOT access CRM
r2 = requests.post(f'{BASE}/api/auth/login/', json={'username': 'staff1', 'password': 'admin123'})
staff_token = r2.json()['access']
sh = {'Authorization': f'Bearer {staff_token}'}
r3 = requests.get(f'{BASE}/api/crm/leads/', headers=sh)
rbac_ok = r3.status_code == 403
print(f'  RBAC (staff blocked from CRM): {"PASS" if rbac_ok else "FAIL"} ({r3.status_code})')
if rbac_ok:
    passed += 1
else:
    failed += 1

print(f'\nResults: {passed} passed, {failed} failed out of {passed + failed} tests')
