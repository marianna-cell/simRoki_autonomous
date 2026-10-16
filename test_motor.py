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

# сброс
requests.post(f"{URL}/reset")
time.sleep(0.5)

print("Начальное состояние:")
s = get_state()
for name, j in s["joints"].items():
    print(f"  {name}: angle={j['angle']:+.3f}, target={j['target']:+.3f}")
print(f"  base: y={s['base']['y']:.3f}, angle={s['base']['angle']:+.3f}")

print("\nШаг 1: сильно выкрутить левое бедро (left_hip = +1.5)")
set_pose([1.5, 0, 0, 0])
time.sleep(1.0)
s = get_state()
print(f"  left_hip angle={s['joints']['left_hip']['angle']:+.3f}, y={s['base']['y']:.3f}")

print("\nШаг 2: сильно выкрутить левое колено (left_knee = −1.5)")
set_pose([0, -1.5, 0, 0])
time.sleep(1.0)
s = get_state()
print(f"  left_knee angle={s['joints']['left_knee']['angle']:+.3f}, y={s['base']['y']:.3f}")

print("\nШаг 3: все суставы в ±1.0")
set_pose([1.0, -1.0, -1.0, 1.0])
time.sleep(1.0)
s = get_state()
for name, j in s["joints"].items():
    print(f"  {name}: angle={j['angle']:+.3f}")
print(f"  base: y={s['base']['y']:.3f}, angle={s['base']['angle']:+.3f}")

print("\nГотово. Смотри в окно — робот должен был шевелиться.")