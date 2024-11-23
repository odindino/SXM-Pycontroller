# SXMDIO.py
import win32file
import win32con
import win32event
import struct


class SXMDIO:
    """
    SXMDIO (SXM Direct I/O) Class
    提供直接從SXM硬體讀取數據的功能

    This class provides direct memory access to SXM hardware data,
    bypassing DDE communication for faster data acquisition.
    """

    def __init__(self):
        """初始化SXMDIO，設定必要的系統常數和建立驅動程式連接"""
        # System Constants
        self.FILE_DEVICE_UNKNOWN = 0x00000022
        self.METHOD_BUFFERED = 0
        self.FILE_ANY_ACCESS = 0x0000

        # Control Codes
        self.IOCTL_GO_XY = self._CTL_CODE(self.FILE_DEVICE_UNKNOWN,
                                          self.METHOD_BUFFERED,
                                          0xF17,
                                          self.FILE_ANY_ACCESS)
        self.IOCTL_SET_CHANNEL = self._CTL_CODE(self.FILE_DEVICE_UNKNOWN,
                                                self.METHOD_BUFFERED,
                                                0xF18,
                                                self.FILE_ANY_ACCESS)
        self.IOCTL_GET_KANAL = self._CTL_CODE(self.FILE_DEVICE_UNKNOWN,
                                              self.METHOD_BUFFERED,
                                              0xF0D,
                                              self.FILE_ANY_ACCESS)
        self.IOCTL_SET_OSZI = self._CTL_CODE(self.FILE_DEVICE_UNKNOWN,
                                             self.METHOD_BUFFERED,
                                             0xF10,
                                             self.FILE_ANY_ACCESS)

        # Scaling factors
        self.x_SF = 6.60667E-6
        self.y_SF = 6.60667E-6
        # self.x_SF = 0.0000106
        # self.y_SF = 0.0000106
        self.TOPO_SF = -8.92967E-7
        self.BIAS_SF = 9.397E-6
        self.ITTOPC_SF = 8.47371E-18

        # Initialize driver connection
        self.initialize_driver()

    def _CTL_CODE(self, DeviceType, Method, Function_code, Access):
        """Generate Windows control code"""
        return (DeviceType << 16) | (Access << 14) | (Function_code << 2) | Method

    def initialize_driver(self):
        """建立與SXM驅動程式的連接"""
        try:
            self.hDriver = win32file.CreateFile(
                r'\\.\SXM',
                win32con.GENERIC_WRITE,
                0,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                0
            )

            # self.GOXY_Event = win32event.CreateEvent(
            #     None,
            #     1,
            #     0,
            #     'Global\\GOXYWAIT\\0'
            # )
            return True
        except Exception as e:
            print(f"Error initializing SXM driver: {str(e)}")
            return False

    def set_channel(self, channel, data):
        """
        設定特定通道的數值

        Parameters
        ----------
        channel : int
            通道編號
        data : int
            要設定的數值
        """
        try:
            D = struct.pack("ll", channel, data)
            win32file.DeviceIoControl(
                self.hDriver,
                self.IOCTL_SET_CHANNEL,
                D,
                0,
                None
            )
        except Exception as e:
            print(f"Error setting channel {channel}: {str(e)}")

    def get_channel(self, channel):
        """
        讀取特定通道的數值

        Parameters
        ----------
        channel : int
            通道編號

        Returns
        -------
        int
            通道數值
        """
        try:
            D = struct.pack("l", channel)
            result = win32file.DeviceIoControl(
                self.hDriver,
                self.IOCTL_GET_KANAL,
                D,
                4,
                None
            )
            return struct.unpack_from("l", result)[0]
        except Exception as e:
            print(f"Error reading channel {channel}: {str(e)}")
            return None

    def get_position(self):
        """
        獲取當前探針位置

        Returns
        -------
        tuple (float, float)
            (x, y) 座標
        """
        try:
            x = self.get_channel(-2)
            y = self.get_channel(-3)
            print(x, y)
            return x*self.x_SF, y*self.y_SF
        except Exception as e:
            print(f"Error getting position: {str(e)}")
            return None, None

    def set_bias(self, bias):
        """
        設定偏壓

        Parameters
        ----------
        bias : float
            偏壓值(mV)
        """
        try:
            bias_raw = int(bias / self.BIAS_SF)
            self.set_channel(33, bias_raw)
        except Exception as e:
            print(f"Error setting bias: {str(e)}")

    def get_bias(self):
        """
        讀取當前偏壓

        Returns
        -------
        float
            偏壓值(mV)
        """
        try:
            bias_raw = self.get_channel(-1)
            return bias_raw * self.BIAS_SF
        except Exception as e:
            print(f"Error reading bias: {str(e)}")
            return None

    def get_tunneling_current(self):
        """
        讀取穿隧電流

        Returns
        -------
        float
            穿隧電流值
        """
        try:
            current_raw = self.get_channel(12)
            return current_raw * self.ITTOPC_SF
        except Exception as e:
            print(f"Error reading tunneling current: {str(e)}")
            return None

    def get_topography(self):
        """
        讀取地形高度(Z方向數據)

        Returns
        -------
        float
            高度值
        """
        try:
            topo_raw = self.get_channel(0)
            return topo_raw * -self.TOPO_SF
        except Exception as e:
            print(f"Error reading topography: {str(e)}")
            return None

    def stop_scan(self):
        """停止掃描"""
        try:
            data_array = [0] * 39
            data_array[4] = -1
            inbuf = struct.pack('l' * 39, *data_array)
            win32file.DeviceIoControl(
                self.hDriver,
                self.IOCTL_GO_XY,
                inbuf,
                32 * 4,
                None
            )
        except Exception as e:
            print(f"Error stopping scan: {str(e)}")
