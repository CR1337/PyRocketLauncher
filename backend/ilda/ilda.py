import ctypes


class HeliosPoint(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_uint16),
        ('y', ctypes.c_uint16),
        ('r', ctypes.c_uint8),
        ('g', ctypes.c_uint8),
        ('b', ctypes.c_uint8),
        ('i', ctypes.c_uint8)
    ]

helios_lib = ctypes.CDLL("backend/ilda/libHeliosDacAPI.so")

helios_lib.OpenDevices.argtypes = []
helios_lib.OpenDevices.restype = ctypes.c_int

helios_lib.GetStatus.argtypes = [ctypes.c_uint]
helios_lib.GetStatus.restype = ctypes.c_int

helios_lib.WriteFrame.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint8, ctypes.POINTER(HeliosPoint), ctypes.c_int]
helios_lib.WriteFrame.restype = ctypes.c_int

helios_lib.SetShutter.argtypes = [ctypes.c_uint, ctypes.c_bool]
helios_lib.SetShutter.restype = ctypes.c_int

helios_lib.GetFirmwareVersion.argtypes = [ctypes.c_uint]
helios_lib.GetFirmwareVersion.restype = ctypes.c_int

helios_lib.GetName.argtypes = [ctypes.c_uint, ctypes.c_char_p]
helios_lib.GetName.restype = ctypes.c_int

helios_lib.SetName.argtypes = [ctypes.c_uint, ctypes.c_char_p]
helios_lib.SetName.restype = ctypes.c_int

helios_lib.Stop.argtypes = [ctypes.c_uint]
helios_lib.Stop.restype = ctypes.c_int

helios_lib.CloseDevices.argtypes = []
helios_lib.CloseDevices.restype = ctypes.c_int

IldaInterface = helios_lib
