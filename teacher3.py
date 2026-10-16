import requests
import random
import time
import json

URL = "http://127.0.0.1:8080"
JOINTS = ["left_hip", "left_knee", "right_hip", "right_knee"]

# ------------------ БАЗА ------------------
def reset():
    requests.post(f"{URL}/reset")
    requests.post(f"{URL}/reset/ball")
    time.sleep(0.4)

def get_state():
    return requests.get(f"{URL}/state").json()

def set_pose(pose):
    body = {"joints": dict(zip(JOINTS, pose))}
    requests.post(f"{URL}/pose", json=body)

def smooth_move(pose_from, pose_to, steps=15, dt=0.03):
    """Плавно перейти из одной позы в другую — без прыжков."""
    for i in range(1, steps + 1):
        t = i / steps
        pose = [a + (b - a) * t for a, b in zip(pose_from, pose_to)]
        set_pose(pose)
        time.sleep(dt)

# ------------------ ЭТАП 1: ПОДЪЁМ ------------------
# Ищем позу, из которой робот встаёт ровно и держится.
# Ключевое: движение должно быть ПЛАВНЫМ.

def evaluate_stand(pose, hold_time=1.5):
    reset()
    time.sleep(0.3)

    # старт — из текущего (лежачего) положения
    start = get_state()
    start_pose = [
        start["joints"]["left_hip"]["angle"],
        start["joints"]["left_knee"]["angle"],
        start["joints"]["right_hip"]["angle"],
        start["joints"]["right_knee"]["angle"],
    ]

    # плавно едем к целевой позе
    smooth_move(start_pose, pose, steps=25, dt=0.03)

    # держим позу
    set_pose(pose)
    time.sleep(hold_time)

    end = get_state()
    y = end["base"]["y"]
    angle = abs(end["base"]["angle"])

    # ЦЕЛЬ: y ~ 1.0 (стоит на ногах), angle маленький (ровный)
    # штраф за резкость не нужен — мы уже плавно двигаемся
    reward = -abs(y - 1.0) * 20.0 - angle * 30.0

    if y < 0.4:          # не встал
        reward -= 100.0
    if y > 1.8:          # улетел
        reward -= 100.0

    return reward, y, angle

POP_SIZE = 14
GENERATIONS = 40

print("ЭТАП 1: учим ПЛАВНО ВСТАВАТЬ и стоять.\n")

def random_stand_pose():
    return [
        random.uniform(-1.2, 1.2),   # left_hip
        random.uniform(-1.5, 0.5),   # left_knee
        random.uniform(-1.2, 1.2),   # right_hip
        random.uniform(-1.5, 0.5),   # right_knee
    ]

population = [random_stand_pose() for _ in range(POP_SIZE)]
best_stand = None

for gen in range(GENERATIONS):
    results = []
    for pose in population:
        r, y, ang = evaluate_stand(pose)
        results.append((r, pose, y, ang))

    results.sort(key=lambda x: x[0], reverse=True)
    best = results[0]
    if best_stand is None or best[0] > best_stand[0]:
        best_stand = best

    print(f"Поколение {gen:2d} | награда={best[0]:8.2f} | y={best[2]:.2f} | angle={best[3]:.2f} | "
          f"pose={[round(p,2) for p in best[1]]}")

    survivors = [r[1] for r in results[:POP_SIZE // 2]]
    new_population = [s[:] for s in survivors]
    while len(new_population) < POP_SIZE:
        p1, p2 = random.sample(survivors, 2)
        child = []
        for j in range(4):
            child.append(p1[j] if random.random() < 0.5 else p2[j])
        for j in range(4):
            if random.random() < 0.5:
                child[j] += random.uniform(-0.15, 0.15)
        new_population.append(child)
    population = new_population

stand_pose = best_stand[1]

with open("stand_pose.json", "w") as f:
    json.dump({"pose": stand_pose}, f, indent=2)

print("\nГОТОВО ЭТАП 1.")
print(f"Поза стойки: {[round(p,2) for p in stand_pose]}")
print(f"Высота: {best_stand[2]:.2f} | Наклон: {best_stand[3]:.2f}")
print("Сохранено в stand_pose.json")