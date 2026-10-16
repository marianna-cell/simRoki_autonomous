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

print("Сброс и отпускаю 2 секунды...")
requests.post(f"{URL}/reset")
time.sleep(2.0)

s = get_state()
print(f"После падения: y={s['base']['y']:.3f}, angle={s['base']['angle']:+.3f}")
print("Суставы:", {k: round(v['angle'],2) for k,v in s['joints'].items()})

print("\nПробую разные позы, смотрю y:\n")

poses = [
    ("все нули",            [0.0, 0.0, 0.0, 0.0]),
    ("servo_zeros",         [-0.394, -0.055, 0.429, -0.030]),
    ("колени назад −0.5",   [0.0, -0.5, 0.0, -0.5]),
    ("колени назад −1.0",   [0.0, -1.0, 0.0, -1.0]),
    ("бёдра прямо, колени −0.8", [0.0, -0.8, 0.0, -0.8]),
    ("бёдра ±0.3, колени −0.8", [0.3, -0.8, -0.3, -0.8]),
]

for name, pose in poses:
    set_pose(pose)
    time.sleep(2.0)
    s = get_state()
    print(f"{name:30s} → y={s['base']['y']:.3f}, angle={s['base']['angle']:+.3f}")