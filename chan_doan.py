"""Chan doan vi sao tao giong cham du da co GPU NVIDIA.

Chay file nay (qua chan_doan_gpu.bat) -> in ra so lieu THAT:
  - torch co dung ban GPU khong, CUDA co bat khong
  - GPU gi, VRAM bao nhieu, dang bi chiem bao nhieu
  - Co bat 'sysmem fallback' (tran VRAM sang RAM -> cham 10-100x) khong
  - Do toc do compute thuan GPU (matmul) -> biet GPU co that su lam viec
  - Do thoi gian TAO GIONG that (cold + warm) -> so sanh voi may chuan ~1-2s

Khong sua gi, khong xoa gi. Chi doc + do.
"""
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def line(): print("-" * 60)

print("=" * 60)
print(" CHAN DOAN GPU - PeiPei Clone Voice")
print("=" * 60)

# --- 1. Torch / CUDA ---
line(); print("[1] PYTORCH & CUDA")
try:
    import torch
except Exception as e:
    print("  [LOI] Khong import duoc torch:", e)
    sys.exit(1)

print("  torch version   :", torch.__version__)
print("  torch.version.cuda:", torch.version.cuda)
cuda_ok = torch.cuda.is_available()
print("  cuda.is_available:", cuda_ok)

if "+cpu" in torch.__version__ or torch.version.cuda is None:
    print("  >>> KET LUAN: Day la ban torch CPU-ONLY. Phai cai lai ban GPU (cu128).")
    sys.exit(0)
if not cuda_ok:
    print("  >>> KET LUAN: torch GPU nhung CUDA=False -> driver loi / GPU bi an.")
    sys.exit(0)

# --- 2. Thong tin GPU ---
line(); print("[2] GPU & VRAM")
dev = torch.device("cuda")
name = torch.cuda.get_device_name(0)
props = torch.cuda.get_device_properties(0)
total = props.total_memory / 1e9
print("  GPU             :", name)
print("  Compute (SM)    :", f"{props.major}.{props.minor}")
print(f"  VRAM tong       : {total:.1f} GB")
free, tot = torch.cuda.mem_get_info()
print(f"  VRAM con trong  : {free/1e9:.1f} GB / {tot/1e9:.1f} GB")
if free/1e9 < 4.0:
    print("  [!] VRAM trong < 4GB -> co the bi app khac chiem (Chrome/game/2 app).")

# --- 3. Sysmem fallback (tran VRAM sang RAM - thu pham cham an tham) ---
line(); print("[3] SYSMEM FALLBACK (tran VRAM -> RAM)")
print("  Neu BAT, khi VRAM gan day GPU se muon RAM he thong -> cham 10-100x.")
print("  Kiem tra trong: NVIDIA Control Panel -> Manage 3D Settings ->")
print("    'CUDA - Sysmem Fallback Policy' -> nen dat 'Prefer No Sysmem Fallback'")
print("  (Hoac dat rieng cho python.exe cua app.)")

# --- 4. Do toc do compute thuan GPU ---
line(); print("[4] TOC DO COMPUTE GPU (matmul 4096x4096)")
try:
    a = torch.randn(4096, 4096, device=dev, dtype=torch.float16)
    b = torch.randn(4096, 4096, device=dev, dtype=torch.float16)
    torch.cuda.synchronize(); t = time.time()
    for _ in range(20):
        c = a @ b
    torch.cuda.synchronize()
    dt = (time.time() - t) / 20 * 1000
    print(f"  Thoi gian moi phep nhan: {dt:.1f} ms")
    if dt < 20:
        print("  >>> GPU compute NHANH (binh thuong).")
    else:
        print("  >>> GPU compute CHAM bat thuong -> nghi tran RAM hoac throttle.")
except Exception as e:
    print("  [LOI] compute test:", e)

# --- 5. Do thoi gian TAO GIONG that ---
line(); print("[5] TAO GIONG THAT (so sanh: may chuan ~1-2s/cau)")
try:
    from app.engine import VoiceEngine
    from app.profiles import ProfileManager
    t = time.time()
    eng = VoiceEngine(); eng.load(log=lambda m: None)
    print(f"  Nap model       : {time.time()-t:.1f}s  (device={eng.device})")
    used = torch.cuda.memory_allocated()/1e9
    print(f"  VRAM model dung : {used:.2f} GB")

    voices = [v["name"] for v in ProfileManager().list()]
    if not voices:
        print("  (Khong co giong da luu de test - bo qua phan tao giong)")
    else:
        prompt = ProfileManager().load_prompt(voices[0])
        TXT = "This is a short test sentence for benchmarking."
        for i in range(1, 4):
            t = time.time()
            eng.generate(TXT, voice_clone_prompt=prompt, language="en", num_step=32)
            g = time.time() - t
            tag = "cold" if i == 1 else "warm"
            print(f"  Tao giong #{i} ({tag}): {g:.1f}s")
        print()
        if g > 10:
            print("  >>> KET LUAN: TAO GIONG CHAM BAT THUONG (cau warm > 10s).")
            print("      Nguyen nhan thuong gap: tran VRAM (sysmem fallback) hoac")
            print("      app khac chiem VRAM. Xem muc [3].")
        else:
            print("  >>> KET LUAN: Toc do BINH THUONG.")
except Exception as e:
    import traceback; traceback.print_exc()
    print("  [LOI] test tao giong:", e)

line()
print("Xong. Chup lai toan bo man hinh nay gui lai de phan tich.")
print("=" * 60)
