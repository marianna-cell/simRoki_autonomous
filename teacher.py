import requests, time
requests.post("http://127.0.0.1:8080/reset")
time.sleep(1.0)
s = requests.get("http://127.0.0.1:8080/state").json()
print(f"y = {s['base']['y']:.3f}")
print(f"angle = {s['base']['angle']:+.3f}")
print(f"углы: {[round(v['angle'],2) for v in s['joints'].values()]}")