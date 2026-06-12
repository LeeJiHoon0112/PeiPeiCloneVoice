"""Chan doan SAU 2: do nvidia-smi NGAY TRONG LUC tao giong de tim thu pham
khien GPU manh nhung inference cham (xung nhip thap, PCIe yeu, GPU khong tai).

Khong sua/xoa gi. Chi do va in so lieu.
"""
import sys, os, time, threading, subprocess, statistics
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def line(): print("-" * 64)

print("=" * 64)
print(" CHAN DOAN 2 - Do GPU NGAY TRONG LUC tao giong")
print("=" * 64)

# --- nvidia-smi: PCIe & clock toi da (do 1 lan, luc ranh) ---
def smi(query):
    try:
        out = subprocess.check_output(
            ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL, timeout=10).decode("utf-8", "replace").strip()
        return out
    except Exception as e:
        return f"(loi nvidia-smi: {e})"

line(); print("[A] PCIe & gioi han phan cung (luc ranh)")
print("  PCIe gen hien tai / toi da :", smi("pcie.link.gen.current"), "/", smi("pcie.link.gen.max"))
print("  PCIe width hien tai / max  :", smi("pcie.link.width.current"), "/", smi("pcie.link.width.max"))
print("  Xung SM hien tai / toi da  :", smi("clocks.current.sm"), "/", smi("clocks.max.sm"), "MHz")
print("  Power gioi han / mac dinh  :", smi("power.limit"), "/", smi("power.default_limit"), "W")
print("  Nhiet do                   :", smi("temperature.gpu"), "C")
print("  >>> Neu PCIe width = 1 (x1) -> day la NGHEN PCIe (slot/riser yeu).")
print("  >>> Neu clocks.current.sm THAP hon nhieu so voi max khi tai -> GPU khong boost.")

# --- Lay mau nvidia-smi lien tuc trong 1 luong rieng ---
samples = {"sm_clock": [], "util": [], "pcie_gen": []}
stop = threading.Event()
def sampler():
    while not stop.is_set():
        try:
            out = subprocess.check_output(
                ["nvidia-smi",
                 "--query-gpu=clocks.current.sm,utilization.gpu,pcie.link.gen.current",
                 "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL, timeout=5).decode("utf-8", "replace").strip()
            parts = [p.strip() for p in out.split(",")]
            if len(parts) >= 2:
                try: samples["sm_clock"].append(float(parts[0]))
                except Exception: pass
                try: samples["util"].append(float(parts[1]))
                except Exception: pass
                if len(parts) >= 3:
                    samples["pcie_gen"].append(parts[2])
        except Exception:
            pass
        time.sleep(0.2)

# --- Nap model + tao giong, do trong luc do ---
line(); print("[B] Nap model va tao giong (dang do nvidia-smi)...")
try:
    from app.engine import VoiceEngine
    from app.profiles import ProfileManager
    eng = VoiceEngine(); eng.load(log=lambda m: None)
    print("  device =", eng.device)
    voices = [v["name"] for v in ProfileManager().list()]
    if not voices:
        print("  (Khong co giong da luu -> khong test duoc. Tao 1 giong roi chay lai.)")
        sys.exit(0)
    prompt = ProfileManager().load_prompt(voices[0])
    TXT = "This is a test sentence used to benchmark the voice generation speed."

    # warm-up 1 lan (bo qua cold start)
    eng.generate(TXT, voice_clone_prompt=prompt, language="en", num_step=32)

    # Do nvidia-smi trong lan tao giong nay
    t0 = time.time()
    th = threading.Thread(target=sampler, daemon=True); th.start()
    eng.generate(TXT, voice_clone_prompt=prompt, language="en", num_step=32)
    dur = time.time() - t0
    stop.set(); th.join(timeout=2)

    line(); print("[C] KET QUA do trong luc tao giong (warm)")
    print(f"  Thoi gian tao 1 cau : {dur:.1f}s  (may chuan ~1.2s)")
    def stat(key, unit=""):
        v = samples[key]
        if not v: return "(khong co mau)"
        return f"min {min(v):.0f}{unit}  /  TB {statistics.mean(v):.0f}{unit}  /  max {max(v):.0f}{unit}"
    print("  Xung SM (MHz)       :", stat("sm_clock"))
    print("  GPU utilization (%) :", stat("util"))
    pg = samples["pcie_gen"]
    print("  PCIe gen luc tai    :", (max(set(pg), key=pg.count) if pg else "(khong co)"))

    line(); print("[D] PHAN TICH TU DONG")
    util = samples["util"]; smc = samples["sm_clock"]
    maxclk = smi("clocks.max.sm")
    if util and statistics.mean(util) < 30:
        print("  >>> GPU utilization THAP (<30%) trong khi tao giong rat lau.")
        print("      => GPU phai NGOI CHO -> nghen o CPU hoac PCIe, KHONG phai GPU yeu.")
    if util and statistics.mean(util) > 80:
        print("  >>> GPU utilization CAO (>80%) -> GPU ban ron that su.")
    try:
        if smc and float(maxclk) > 0 and statistics.mean(smc) < 0.6 * float(maxclk):
            print(f"  >>> Xung SM TB ({statistics.mean(smc):.0f}) thap hon 60% max ({maxclk})")
            print("      => GPU KHONG BOOST (power management). Xem cach sua ben duoi.")
    except Exception:
        pass
    print()
    print("  Cach sua thuong gap:")
    print("   - NVIDIA Control Panel -> Manage 3D Settings -> Power management mode")
    print("     -> 'Prefer Maximum Performance'.")
    print("   - Windows: Settings -> System -> Power -> 'Best performance'.")
    print("   - Neu PCIe width = x1: chuyen card sang khe PCIe x16 chinh cua main.")
except Exception as e:
    stop.set()
    import traceback; traceback.print_exc()
    print("  [LOI]:", e)

line()
print("Xong. CHUP TOAN BO man hinh nay gui lai.")
print("=" * 64)
