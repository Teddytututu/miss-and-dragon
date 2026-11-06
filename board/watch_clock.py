"""Optional Windows boot-session sleep counter, in milliseconds."""
import ctypes
import os


def sleep_milliseconds():
    if os.name != 'nt':return None
    try:
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetTickCount64.restype = ctypes.c_ulonglong
        kernel.QueryUnbiasedInterruptTime.argtypes = [ctypes.POINTER(ctypes.c_ulonglong)]
        kernel.QueryUnbiasedInterruptTime.restype = ctypes.c_int
        awake = ctypes.c_ulonglong()
        if not kernel.QueryUnbiasedInterruptTime(ctypes.byref(awake)):return None
        return max(0, kernel.GetTickCount64()-awake.value//10000)
    except (AttributeError, OSError):
        return None
