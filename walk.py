import requests
import time

URL = "http://127.0.0.1:8080"
JOINTS = ["left_hip", "left_knee", "right_hip", "right_knee"]

def reset():
    requests.post(f"{URL}/reset")
    time.sleep(0.5)

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

def smooth_to(target, steps=60, dt=0.04):
    """Плавно едем в целевую позу."""
    start = get_current_pose()
    for i in range(1, steps + 1):
        t = i / steps
        t_smooth = t * t * (3 - 2 * t)
        pose = [a + (b - a) * t_smooth for a, b in zip(start, target)]
        set_pose(pose)
        time.sleep(dt)

# --- СРЕДНЯЯ СТОЙКА ---
# Из тестов мы знаем: servo_zeros = [-0.394, -0.055, 0.429, -0.030]
# Это калибровка робота — близко к вертикали.
# Попробуем её как базу и слегка доработаем.

STANCE = [-0.394, -0.055, 0.429, -0.030]

# --- ПОХОДКА ---
# Простая противофазная походка.
# Фаза 0: обе ноги на земле (стоя)
# Фаза 1: левая вперёд, правая опора
# Фаза 2: обе на земле
# Фаза 3: правая вперёд, левая опора

SWING = 0.5      # насколько сильно выносим ногу вперёд
LIFT  = 0.6      # насколько сильно поднимаем колено

def make_cycle(stance, swing, lift):
    lh, lk, rh, rk = stance
    return [
        # фаза 0 — стоим
        [lh,        lk,         rh,        rk],
        # фаза 1 — левая вперёд
        [lh + swing, lk - lift, rh,        rk],
        # фаза 2 — стоим (левая впереди)
        [lh + swing, lk,        rh,        rk],
        # фаза 3 — правая вперёд
        [lh,        lk,         rh + swing, rk - lift],
    ]

# --- ЗАПУСК ---
print("Сброс...")
reset()
time.sleep(0.5)

print("Плавный подъём в среднюю стойку (3 секунды)...")
smooth_to(STANCE, steps=60, dt=0.05)

s = get_state()
print(f"После подъёма: y={s['base']['y']:.3f}, angle={s['base']['angle']:+.3f}")
print(f"Суставы: {[round(x,2) for x in get_current_pose()]}\n")

print("Стою 1 секунду...")
time.sleep(1.0)

s = get_state()
print(f"Перед ходьбой: y={s['base']['y']:.3f}, angle={s['base']['angle']:+.3f}\n")

print("Начинаю шагать. Смотри в окно! (Ctrl+C для остановки)\n")

cycle = make_cycle(STANCE, SWING, LIFT)
DT = 0.25   # длительность одной фазы

try:
    step = 0
    while True:
        for pose in cycle:
            set_pose(pose)
            time.sleep(DT)

        step += 1
        if step % 4 == 0:
            s = get_state()
            print(f"Шаг {step:3d} | x={s['base']['x']:7.2f} | y={s['base']['y']:.3f} | angle={s['base']['angle']:+.3f}")

        # если упал — сброс и снова встать
        if s["base"]["y"] < 0.3:
            print(f"  ⚠ упал на шаге {step}, сбрасываю...")
            reset()
            time.sleep(0.5)
            smooth_to(STANCE, steps=60, dt=0.05)
            time.sleep(0.5)

except KeyboardInterrupt:
    print("\nОстановлено.")

final = get_state()
print(f"Финал: x={final['base']['x']:.2f}, y={final['base']['y']:.3f}, angle={final['base']['angle']:+.3f}")