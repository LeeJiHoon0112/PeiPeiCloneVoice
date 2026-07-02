# -*- coding: utf-8 -*-
"""Build-time: tao 'Python nhung' (embeddable Python 3.13) da bat pip + site-packages.

Chay boi build.bat BANG PYTHON DEV. Output: <target>/python/ (CHUA co deps nang —
torch/omnivoice... se cai o may khach lan dau qua setup.bat).

Sau buoc nay, thu muc python/ la mot Python 3.13 di dong (relocatable):
  - ._pth: them 'Lib\\site-packages' (cho pip) + '..' (de thay app.pyd & main.py o thu muc cha).
  - da co pip.
"""
import io
import os
import subprocess
import sys
import urllib.request
import zipfile

PY_VER = "3.13.9"   # PHAI khop minor 3.13 voi file .pyd (cp313)
EMBED_URL = f"https://www.python.org/ftp/python/{PY_VER}/python-{PY_VER}-embed-amd64.zip"
GETPIP_URL = "https://bootstrap.pypa.io/get-pip.py"
# Tag phien ban theo PY_VER (vd "3.13.9" -> "313") — dung cho ten pythonXYY.zip / ._pth.
_TAG = "".join(PY_VER.split(".")[:2])          # "313"
_PTH_FILE = f"python{_TAG}._pth"
PTH = f"python{_TAG}.zip\n.\nLib\\site-packages\n..\nimport site\n"


def _download(url):
    print("  tai:", url)
    with urllib.request.urlopen(url) as r:
        return r.read()


def main(target):
    pydir = os.path.join(target, "python")
    # Cache HỢP LỆ chỉ khi có python.exe VÀ đúng bản (có pythonXYY.zip khớp PY_VER). Nếu đổi
    # PY_VER mà cache là bản cũ -> XÓA cache + tải lại (tránh release chứa Python KHÔNG khớp .pyd).
    if os.path.exists(os.path.join(pydir, "python.exe")):
        if os.path.exists(os.path.join(pydir, f"python{_TAG}.zip")):
            print("[skip] da co (dung ban)", pydir)
            return
        print(f"[cache cu != {PY_VER}] xoa {pydir} de tai lai...")
        import shutil
        shutil.rmtree(pydir, ignore_errors=True)
    os.makedirs(pydir, exist_ok=True)
    print(f"[1/3] Tai + giai nen Python nhung {PY_VER}...")
    zipfile.ZipFile(io.BytesIO(_download(EMBED_URL))).extractall(pydir)
    print("[2/3] Bat site-packages + thu muc cha trong ._pth...")
    with open(os.path.join(pydir, _PTH_FILE), "w", encoding="ascii") as f:
        f.write(PTH)
    print("[3/3] Cai pip...")
    gp = os.path.join(pydir, "get-pip.py")
    with open(gp, "wb") as f:
        f.write(_download(GETPIP_URL))
    subprocess.check_call([os.path.join(pydir, "python.exe"), gp,
                           "--no-warn-script-location"])
    os.remove(gp)
    print("XONG -> Python nhung tai:", pydir)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/python_base")
