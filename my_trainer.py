import requests
import random
import time

URL = "http://127.0.0.1:8080"

def get_state():
    return requests.get(f"{URL}/state").json()

def send_action(angles_deg, repeat=10):
    data = {"action_deg": angles_deg, "repeat_steps": repeat}
    return requests.post(f"{URL}/rl/step", json=data).json()

def reset():
    requests.post(f"{URL}/reset")

def calculate_reward(state, prev_x):
    reward = 0.0
    base = state["base"]
    joints = state["joints"]

    dx = base["x"] - prev_x
    reward += dx * 100.0

    if base["y"] < 0.5:
        reward -= 50.0

    reward -= abs(base["angle"]) * 5.0

    for j in joints.values():
        reward -= abs(j["torque"]) * 0.01

    reward += 0.5
    return reward


# --- ЗАПУСК ---
print("Сбрасываю робота...")
reset()
time.sleep(0.5)

state = get_state()
prev_x = state["base"]["x"]
total_reward = 0.0

print("Начинаю случайные движения. Смотри в окно симулятора!")
print("Остановить — Ctrl+C в терминале.\n")

for step in range(200):
    # случайные углы в диапазоне ±30 градусов от нуля
    angles = [random.uniform(-30, 30) for _ in range(4)]

    state = send_action(angles, repeat=10)

    reward = calculate_reward(state, prev_x)
    total_reward += reward

    prev_x = state["base"]["x"]

    print(f"Шаг {step:3d} | x = {prev_x:6.2f} | награда = {reward:7.2f} | сумма = {total_reward:8.2f}")

    if state["base"]["y"] < 0.3:
        print(">>> Робот упал, сбрасываю...")
        reset()
        time.sleep(0.5)
        state = get_state()
        prev_x = state["base"]["x"]

print("\nГотово.")