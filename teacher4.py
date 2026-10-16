import requests
import time

URL = "http://127.0.0.1:8080"
JOINTS = ["left_hip", "left_knee", "right_hip", "right_knee"]

def reset():
    requests.post(f"{URL}/reset")
    time.sleep(0.4)

def get_state():
    return requests.get(f"{URL}/state").json()

def set_pose(pose):
    body = {"joints": dict(zip(JOINTS, pose))}
    return requests.post(f"{URL}/pose", json=body).json()

def get_current_pose():
    s = get_state()
    return [
        s["joints"]["left_hip"]["angle"],
        s["joints"]["left_knee"]["angle"],
        s["joints"]["right_hip"]["angle"],
        s["joints"]["right_knee"]["angle"],
    ]

def get_servo_zeros():
    s = get_state()
    z = s["servo_zeros"]
    return [z["left_hip"], z["left_knee"], z["right_hip"], z["right_knee"]]

# --- СТОЙКА = SERVO ZEROS ---
def smooth_lift(target, steps=100, dt=0.05):
    start = get_current_pose()
    for i in range(1, steps + 1):
        t = i / steps
        t_smooth = t * t * (3 - 2 * t)
        pose = [a + (b - a) * t_smooth for a, b in zip(start, target)]
        set_pose(pose)
        time.sleep(dt)

# --- ЗАПУСК ---
print("Сброс...")
reset()
time.sleep(0.5)

print("Читаю servo_zeros (это вертикальная стойка робота)...")
STANCE = get_servo_zeros()
print(f"STANCE = {[round(x, 3) for x in STANCE]}")

print("\nПлавный подъём в эту позу (5 секунд)...")
smooth_lift(STANCE, steps=100, dt=0.05)

print("\nДержу стойку БЕЗ баланса 8 секунд, пишу наклон:\n")

start_time = time.time()
while time.time() - start_time < 8.0:
    s = get_state()
    y = s["base"]["y"]
    angle = s["base"]["angle"]
    omega = s["base"]["omega"]
    vx = s["base"]["vx"]

    print(f"t={time.time()-start_time:4.1f}s | "
          f"y={y:5.2f} | angle={angle:+6.3f} | omega={omega:+6.3f} | vx={vx:+6.3f}")

    if y < 0.4:
        print(">>> УПАЛ")
        break

    set_pose(STANCE)
    time.sleep(0.1)

print("\nГотово.")