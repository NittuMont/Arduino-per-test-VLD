"""
Benchmark SCPI round-trip times against the ITech power supply.

Tests (in order):
  1. set_voltage round-trip (no output, just send)
  2. measure_voltage round-trip (query)
  3. Combined: set_voltage + measure_voltage (simulates innesco step)
  4. Burst: 30 consecutive steps at 10V→40V, measuring each

Usage:
    python bench_scpi.py [host] [port]
    python bench_scpi.py 192.168.1.100
"""

import sys
import time
import statistics
import socket

# Import diretto senza passare per __init__.py (evita dipendenza da openpyxl/PyQt5)
sys.path.insert(0, r"c:\Users\AntonioDeGiudici\ITECH VLD\itech_interface\src")

# Carica solo i moduli necessari
import importlib.util, types

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

BASE = r"c:\Users\AntonioDeGiudici\ITECH VLD\itech_interface\src\itech_interface"
network = _load("itech_interface.network", BASE + r"\network.py")
# controller dipende da network, già in sys.modules
ctrl_mod = _load("itech_interface.controller", BASE + r"\controller.py")

ITechConnection = network.ITechConnection
PowerSupplyController = ctrl_mod.PowerSupplyController

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5025
N = 30  # ripetizioni per ogni test

def hline(title=""):
    print(f"\n{'─'*55}")
    if title:
        print(f"  {title}")
        print(f"{'─'*55}")

def stats(label, times_ms):
    mn  = min(times_ms)
    mx  = max(times_ms)
    avg = statistics.mean(times_ms)
    med = statistics.median(times_ms)
    p90 = sorted(times_ms)[int(len(times_ms)*0.9)]
    print(f"  {label:<30}  min={mn:5.1f}  med={med:5.1f}  avg={avg:5.1f}  p90={p90:5.1f}  max={mx:5.1f}  ms")

print(f"\nConnessione a {HOST}:{PORT} ...")
conn = ITechConnection(HOST, PORT, timeout=2.0)
conn.connect()
ctrl = PowerSupplyController(conn)
print("Connesso.\n")

# --- 1. set_voltage solo ---
hline("1. set_voltage (senza output attivo)")
t_set = []
for _ in range(N):
    t0 = time.perf_counter()
    ctrl.set_voltage(15)
    t_set.append((time.perf_counter() - t0) * 1000)
stats("set_voltage", t_set)

# --- 2. measure_voltage solo ---
hline("2. measure_voltage (query)")
t_meas = []
for _ in range(N):
    t0 = time.perf_counter()
    ctrl.measure_voltage()
    t_meas.append((time.perf_counter() - t0) * 1000)
stats("measure_voltage", t_meas)

# --- 3. Coppia set + measure ---
hline("3. set_voltage + measure_voltage (come ogni step innesco)")
t_pair = []
for _ in range(N):
    t0 = time.perf_counter()
    ctrl.set_voltage(15)
    ctrl.measure_voltage()
    t_pair.append((time.perf_counter() - t0) * 1000)
stats("set + measure", t_pair)

# --- 4. Burst 30 steps 10V→40V con output ON ---
hline("4. Burst realístico: 30 step 10V→40V (output ON, misura ogni step)")
ctrl.set_voltage(10)
ctrl.set_current(0.1)   # corrente bassa per sicurezza
ctrl.output_on()
time.sleep(0.3)

t_burst = []
for v in range(10, 40):
    t0 = time.perf_counter()
    ctrl.set_voltage(v)
    ctrl.measure_voltage()
    elapsed = (time.perf_counter() - t0) * 1000
    t_burst.append(elapsed)
    print(f"    V={v:3d}V  →  {elapsed:6.1f} ms")

ctrl.output_off()
ctrl.local_mode()

hline("Riepilogo burst")
stats("step (set+meas, output ON)", t_burst)

hline()
total = statistics.mean(t_pair)
print(f"\n  Stima intervallo medio per step innesco (set+meas): {total:.1f} ms")
print(f"  Con singleShot(0): intervallo atteso  ~{total:.0f} ms")
print(f"  Con singleShot(100): intervallo atteso ~{total+100:.0f} ms")
print()
conn.disconnect()
