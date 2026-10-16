import requests
import time

URL = "http://127.0.0.1:8080"

def get_state():
    return requests.get(f"{URL}/state").json()

def set_pose(pose):
    body = {"joints": {
        "left_hip": pose[0], "left_knee": pose[1],
        "right_hip": pose[2], "right_knee": pose[3]
    }}
    return requests.post(f"{URL}/pose", json=body).json()

# пробуем найти "suspend" через разные эндпоинты
print("Пробую разные команды для подвеса:\n")

for ep in ["/suspend", "/release", "/hang", "/drop", "/debug/suspend"]:
    r = requests.post(f"{URL}{ep}")
    print(f"POST {ep} → {r.status_code}")

print("\nПробую GET-версии:")
for ep in ["/suspend", "/mode", "/debug"]:
    r = requests.get(f"{URL}{ep}")
    print(f"GET {ep} → {r.status_code} ({r.text[:80]})")

print("\nЧто говорит /state после этого:")
s = get_state()
print(f"y={s['base']['y']:.3f}, angle={s['base']['angle']:+.3f}, mode={s.get('mode','?')}")