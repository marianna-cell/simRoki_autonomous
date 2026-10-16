import requests
import random
import time
import json
import math

URL = "http://127.0.0.1:8080"
JOINTS = ["left_hip", "left_knee", "right_hip", "right_knee"]

def reset():
    requests.post(f"{URL}/reset")
    requests.post(f"{URL}/reset/ball")
    time.sleep(0.3)

def get_state():
    return requests.get(f"{URL}/state").json()

def set_pose(pose):
    body = {"joints": dict(zip(JOINTS, pose))}
    requests.post(f"{URL}/pose", json=body)

# -------- ПОСТРОЕНИЕ ПРЯМОЙ ПОХОДКИ --------
# Параметры походки (то, что учим):
#   stance_hip    — угол бедра в стойке (насколько отведено назад)
#   swing_hip     — угол бедра в шаге (насколько вынесено вперёд)
#   lift_knee     — насколько сгибается колено в шаге (подъём ноги)
#   body_lean     — небольшой наклон корпуса вперёд для движения
#
# Строим 4 фазы походки. Левая и правая ноги работают в противофазе.

def build_cycle(params):
    stance_hip, swing_hip, lift_knee, body_lean = params

    # ФАЗА 0: стойка (обе ноги на земле)
    p0 = [
        stance_hip,            # left_hip
        -0.05,                 # left_knee (чуть согнут)
        stance_hip,            # right_hip
        -0.05,                 # right_knee
    ]

    # ФАЗА 1: левая выносится вперёд, правая опора
    p1 = [
        swing_hip,             # left_hip вперёд
        -lift_knee,            # left_knee поднят
        stance_hip,            # right_hip назад
        -0.05,                 # right_knee опора
    ]

    # ФАЗА 2: снова стойка (левая приземлилась)
    p2 = [
        swing_hip,             # left_hip впереди
        -0.05,
        stance_hip,            # right_hip сзади
        -0.05,
    ]

    # ФАЗА 3: правая выносится вперёд, левая опора
    p3 = [
        swing_hip,             # left_hip впереди
        -0.05,
        swing_hip,             # right_hip вперёд
        -lift_knee,            # right_knee поднят
    ]

    return [p0, p1, p2, p3]

def run_cycle(cycle, dt=0.15, repeats=5):
    for _ in range(repeats):
        for pose in cycle:
            set_pose(pose)
            time.sleep(dt)

def evaluate(params, dt=0.15, repeats=6):
    cycle = build_cycle(params)
    reset()
    time.sleep(0.3)
    start = get_state()
    start_x = start["base"]["x"]

    run_cycle(cycle, dt, repeats)

    end = get_state()
    dx = end["base"]["x"] - start_x
    y = end["base"]["y"]
    angle = abs(end["base"]["angle"])

    if y > 2.0 or y < 0.3:
        return -100.0, dx, y, angle

    # ЦЕНИМ: движение вперёд + ровная высота + минимальный наклон
    reward = (
        dx * 20.0
        - angle * 20.0
        - abs(y - 1.0) * 8.0
    )
    return reward, dx, y, angle

# --- ПАРАМЕТРЫ ОБУЧЕНИЯ ---
POP_SIZE = 14
GENERATIONS = 60
DT = 0.15
REPEATS = 6

print("Учим ПРЯМУЮ походку. Смотри в окно симулятора!\n")

def random_params():
    return [
        random.uniform(-0.6, 0.6),   # stance_hip
        random.uniform(-1.0, 1.0),   # swing_hip
        random.uniform(0.2, 1.0),    # lift_knee
        random.uniform(-0.2, 0.2),   # body_lean (пока не используем)
    ]

population = [random_params() for _ in range(POP_SIZE)]
best_overall = None

for gen in range(GENERATIONS):
    results = []
    for params in population:
        r, dx, y, ang = evaluate(params, DT, REPEATS)
        results.append((r, params, dx, y, ang))

    results.sort(key=lambda x: x[0], reverse=True)
    best = results[0]
    if best_overall is None or best[0] > best_overall[0]:
        best_overall = best

    print(
        f"Поколение {gen:2d} | награда={best[0]:8.2f} | "
        f"dx={best[2]:6.2f} | y={best[3]:.2f} | angle={best[4]:.2f} | "
        f"params={[round(p,2) for p in best[1]]}"
    )

    survivors = [r[1] for r in results[:POP_SIZE // 2]]

    new_population = [s[:] for s in survivors]
    while len(new_population) < POP_SIZE:
        p1, p2 = random.sample(survivors, 2)
        child = []
        for j in range(4):
            child.append(p1[j] if random.random() < 0.5 else p2[j])
        for j in range(4):
            if random.random() < 0.5:
                child[j] += random.uniform(-0.1, 0.1)
        new_population.append(child)

    population = new_population

# сохраняем лучшую походку
best_cycle = build_cycle(best_overall[1])
with open("best_gait.json", "w") as f:
    json.dump(
        {
            "dt": DT,
            "repeats": REPEATS,
            "params": best_overall[1],
            "steps": [{"pose": p} for p in best_cycle],
        },
        f,
        indent=2,
    )

print("\nГотово. Походка сохранена в best_gait.json")
print(f"Параметры: stance_hip={best_overall[1][0]:.2f}, "
      f"swing_hip={best_overall[1][1]:.2f}, "
      f"lift_knee={best_overall[1][2]:.2f}")
print(f"Лучший dx за {REPEATS} циклов: {best_overall[2]:.2f} м")
print(f"Наклон: {best_overall[4]:.2f} | Высота: {best_overall[3]:.2f}")