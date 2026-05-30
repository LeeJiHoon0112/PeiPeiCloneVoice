"""Chạy các tác vụ nặng (nạp model, ASR, sinh audio) trên luồng nền để UI không bị treo."""
from PyQt5.QtCore import QThread, pyqtSignal


class Task(QThread):
    """Chạy một hàm bất kỳ trên luồng nền.

    - done(object):      phát ra khi thành công, kèm kết quả trả về của hàm
    - failed(str):       phát ra khi lỗi, kèm thông báo
    - log(str):          thông báo tiến độ dạng chữ (hàm nhận tham số `log=`)
    - progress(int,int): (đã_xong, tổng) để vẽ thanh % (hàm nhận tham số `progress=`)
    """

    done = pyqtSignal(object)
    failed = pyqtSignal(str)
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)

    def __init__(self, fn, *args, pass_log=False, pass_progress=False, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._pass_log = pass_log
        self._pass_progress = pass_progress

    def run(self):
        try:
            if self._pass_log:
                self._kwargs["log"] = self.log.emit
            if self._pass_progress:
                self._kwargs["progress"] = self.progress.emit
            result = self._fn(*self._args, **self._kwargs)
            self.done.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.failed.emit(f"{type(e).__name__}: {e}")
