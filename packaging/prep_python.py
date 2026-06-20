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
# Noi dung ._pth: bat site-packages + thu muc cha (chua app.pyd/main.py).
PTH = "python313.zip\n.\nLib\\site-packages\n..\nimport site\n"


def _download(url):
    print("  tai:", url)
    with urllib.request.urlopen(url) as r:
        return r.read()


def main(target):
    pydir = os.path.join(target, "python")
    if os.path.exists(os.path.join(pydir, "python.exe")):
        print("[skip] da co", pydir)
        return
    os.makedirs(pydir, exist_ok=True)
    print(f"[1/3] Tai + giai nen Python nhung {PY_VER}...")
    zipfile.ZipFile(io.BytesIO(_download(EMBED_URL))).extractall(pydir)
    print("[2/3] Bat site-packages + thu muc cha trong ._pth...")
    with open(os.path.join(pydir, "python313._pth"), "w", encoding="ascii") as f:
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
