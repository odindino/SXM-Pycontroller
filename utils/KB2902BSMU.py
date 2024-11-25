"""
Keysight B2902B Source Measure Unit (SMU) Control Library

This library provides a comprehensive interface for controlling the Keysight B2902B SMU.
It includes functions for basic operations like voltage/current sourcing and measurement,
as well as advanced features for system configuration and error handling.

Author: Zi-Liang Yang
Version: 1.0.0
Date: 2024-11-25
"""

import pyvisa
import time
import logging
from typing import Optional, Tuple, Union, List
from enum import Enum

class Channel(Enum):
    """Enumeration for SMU channels"""
    CH1 = 1
    CH2 = 2

class OutputMode(Enum):
    """Enumeration for output modes"""
    VOLTAGE = 'VOLT'
    CURRENT = 'CURR'

class ConnectionError(Exception):
    """Exception raised for connection-related errors"""
    pass

class MeasurementError(Exception):
    """Exception raised for measurement-related errors"""
    pass

class KeysightB2902B:
    """
    Keysight B2902B SMU Control Class
    
    This class provides a comprehensive interface for controlling the B2902B SMU,
    including voltage/current sourcing, measurement, and system configuration.
    
    Attributes:
        resource_name (str): VISA resource name for the instrument
        smu (pyvisa.Resource): PyVISA resource object
        logger (logging.Logger): Logger for recording operations and errors
    """
    
    def __init__(self, resource_name: str = None, timeout: int = 10000):
        """
        Initialize the SMU controller
        
        Args:
            resource_name (str): VISA resource name (e.g., 'TCPIP0::172.30.32.98::inst0::INSTR')
            timeout (int): Communication timeout in milliseconds
        """
        self.resource_name = resource_name
        self.timeout = timeout
        self.smu = None
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    # def connect(self, resource_name: str = None) -> bool:
    #     """
    #     Connect to the SMU
        
    #     Args:
    #         resource_name (str, optional): VISA resource name if different from initialization
            
    #     Returns:
    #         bool: True if connection successful, False otherwise
            
    #     Raises:
    #         ConnectionError: If connection fails
    #     """
    #     try:
    #         rm = pyvisa.ResourceManager()
    #         self.resource_name = resource_name or self.resource_name
            
    #         if not self.resource_name:
    #             raise ConnectionError("No resource name provided")
                
    #         self.smu = rm.open_resource(self.resource_name, timeout=self.timeout)
            
    #         # Reset and clear the instrument
    #         self.smu.write("*RST")
    #         self.smu.write("*CLS")
            
    #         # Verify connection by reading ID
    #         idn = self.smu.query("*IDN?")
    #         self.logger.info(f"Connected to: {idn.strip()}")
            
    #         # Enable system beeper
    #         self.enable_beeper(True)
            
    #         return True
            
    #     except Exception as e:
    #         self.logger.error(f"Connection failed: {str(e)}")
    #         raise ConnectionError(f"Failed to connect to SMU: {str(e)}")
    def connect(self, resource_name: str = None) -> bool:
        try:
            self.rm = pyvisa.ResourceManager()
            self.resource_name = resource_name or self.resource_name
            
            if not self.resource_name:
                raise ConnectionError("No resource name provided")
                
            # 配置儀器連接
            self.smu = self.rm.open_resource(self.resource_name)
            self.smu.timeout = 10000  # 增加超時時間
            self.smu.read_termination = '\n'
            self.smu.write_termination = '\n'
            self.smu.chunk_size = 102400  # 增加讀取緩衝區大小
            
            # 配置測量參數
            self.smu.write("*RST")
            self.smu.write("*CLS")
            self.smu.write(":FORM:DATA ASC")  # 使用ASCII格式
            self.smu.write(":SENS:CURR:NPLC 0.1")  # 快速測量模式
            self.smu.write(":SENS:VOLT:NPLC 0.1")
            
            idn = self.smu.query("*IDN?")
            self.logger.info(f"Connected to: {idn.strip()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False

    def disconnect(self):
        """
        Safely disconnect from the SMU
        """
        if self.smu:
            try:
                # Turn off all outputs before disconnecting
                for channel in Channel:
                    self.disable_output(channel)
                self.smu.close()
                self.logger.info("Disconnected from SMU")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {str(e)}")

    def check_connection(self) -> bool:
        """
        Check if the connection to the SMU is active
        
        Returns:
            bool: True if connected and responsive
        """
        if not self.smu:
            return False
            
        try:
            self.smu.query("*IDN?")
            return True
        except:
            return False

    def configure_source(self, 
                        channel: Channel,
                        mode: OutputMode,
                        level: float,
                        compliance: float,
                        auto_range: bool = True) -> bool:
        """
        Configure the source parameters for a channel
        
        Args:
            channel (Channel): Channel to configure
            mode (OutputMode): VOLTAGE or CURRENT
            level: Source level (V or A)
            compliance: Compliance level (A for voltage source, V for current source)
            auto_range (bool): Enable auto-ranging
            
        Returns:
            bool: True if configuration successful
        """
        try:
            ch = channel.value
            mode_str = mode.value
            
            # Configure source mode and level
            self.smu.write(f":SOUR{ch}:FUNC:MODE {mode_str}")
            self.smu.write(f":SOUR{ch}:{mode_str} {level}")
            
            # Set compliance based on mode
            comp_mode = "CURR" if mode == OutputMode.VOLTAGE else "VOLT"
            self.smu.write(f":SENS{ch}:{comp_mode}:PROT {compliance}")
            
            # Configure ranging
            if auto_range:
                self.smu.write(f":SOUR{ch}:{mode_str}:RANG:AUTO ON")
            
            self.logger.info(
                f"Channel {ch} configured: {mode_str} = {level}, "
                f"Compliance = {compliance}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration error: {str(e)}")
            return False

    def enable_output(self, channel: Channel) -> bool:
        """Enable output for specified channel"""
        try:
            self.smu.write(f":OUTP{channel.value} ON")
            time.sleep(0.1)  # Wait for output to stabilize
            
            if int(self.smu.query(f"OUTP{channel.value}?")):
                self.logger.info(f"Channel {channel.value} output enabled")
                return True
            else:
                self.logger.error(f"Failed to enable channel {channel.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"Output enable error: {str(e)}")
            return False

    def disable_output(self, channel: Channel) -> bool:
        """Disable output for specified channel"""
        try:
            self.smu.write(f":OUTP{channel.value} OFF")
            time.sleep(0.1)
            
            if not int(self.smu.query(f"OUTP{channel.value}?")):
                self.logger.info(f"Channel {channel.value} output disabled")
                return True
            else:
                self.logger.error(f"Failed to disable channel {channel.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"Output disable error: {str(e)}")
            return False

    # def measure(self, 
    #            channel: Channel,
    #            parameters: List[str] = None) -> Union[float, Tuple[float, ...]]:
    #     """
    #     Perform measurements on specified channel
        
    #     Args:
    #         channel (Channel): Channel to measure
    #         parameters (List[str]): List of parameters to measure ('VOLT', 'CURR', 'RES')
    #                               If None, measures all parameters
        
    #     Returns:
    #         Union[float, Tuple[float, ...]]: Measured values
    #     """
    #     if parameters is None:
    #         parameters = ['VOLT', 'CURR', 'RES']
            
    #     try:
    #         results = []
    #         for param in parameters:
    #             value = float(self.smu.query(f":MEAS:{param}? (@{channel.value})"))
    #             results.append(value)
                
    #         return results[0] if len(results) == 1 else tuple(results)
            
    #     except Exception as e:
    #         self.logger.error(f"Measurement error: {str(e)}")
    #         raise MeasurementError(f"Failed to measure: {str(e)}")
    def measure(self, channel: Channel, parameters: List[str] = None) -> List[float]:
        """執行測量"""
        if parameters is None:
            parameters = ['VOLT', 'CURR']
            
        try:
            results = []
            for param in parameters:
                # 清除之前的狀態
                self.smu.write("*CLS")
                
                # 配置測量
                self.smu.write(f":CONF:{param} (@{channel.value})")
                self.smu.write(":FORM:ELEM:SENS VOLT,CURR")
                
                # 執行測量
                value = float(self.smu.query(f":MEAS:{param}? (@{channel.value})"))
                results.append(value)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Measurement error: {str(e)}")
            raise MeasurementError(f"Failed to measure: {str(e)}")

    def get_error(self) -> Optional[str]:
        """
        Read and return error message from the instrument
        
        Returns:
            Optional[str]: Error message if any, None if no error
        """
        try:
            error = self.smu.query(":SYST:ERR:ALL?")
            if error.startswith("+0"):  # No error
                return None
            return error.strip()
        except Exception as e:
            self.logger.error(f"Error query failed: {str(e)}")
            return None

    def enable_beeper(self, enable: bool = True):
        """Enable or disable the system beeper"""
        try:
            self.smu.write(f":SYST:BEEP:STAT {'ON' if enable else 'OFF'}")
        except Exception as e:
            self.logger.error(f"Beeper control error: {str(e)}")

    def beep(self, frequency: int = 440, duration: float = 0.1):
        """
        Generate a beep sound
        
        Args:
            frequency (int): Beep frequency in Hz (20-20000)
            duration (float): Beep duration in seconds (0.01-5.0)
        """
        try:
            self.smu.write(f":SYST:BEEP {frequency},{duration}")
        except Exception as e:
            self.logger.error(f"Beep error: {str(e)}")

    def set_nplc(self, channel: Channel, nplc: float):
        """
        Set the integration time in number of power line cycles (NPLC)
        
        Args:
            channel (Channel): Target channel
            nplc (float): Integration time in PLCs (0.01-10)
        """
        try:
            self.smu.write(f":SENS{channel.value}:CURR:NPLC {nplc}")
            self.smu.write(f":SENS{channel.value}:VOLT:NPLC {nplc}")
        except Exception as e:
            self.logger.error(f"NPLC setting error: {str(e)}")

    def get_system_status(self) -> dict:
        """
        Get comprehensive system status
        
        Returns:
            dict: System status information
        """
        status = {
            'connected': self.check_connection(),
            'channels': {}
        }
        
        if status['connected']:
            for channel in Channel:
                ch = channel.value
                try:
                    status['channels'][ch] = {
                        'output': bool(int(self.smu.query(f"OUTP{ch}?"))),
                        'source_mode': self.smu.query(f":SOUR{ch}:FUNC:MODE?").strip(),
                        'error': self.get_error()
                    }
                except:
                    status['channels'][ch] = {'error': 'Failed to read status'}
                    
        return status

    def __enter__(self):
        """Context manager entry"""
        if not self.smu:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def _send_command(self, command: str, check_errors: bool = True) -> Tuple[bool, Optional[str]]:
        """Send SCPI command to instrument with error checking

        Args:
            command (str): SCPI command string
            check_errors (bool, optional): Whether to check for errors after command. Defaults to True.

        Returns:
            Tuple[bool, Optional[str]]: Success status and error message if any
        """
        try:
            # Check connection status
            if not self.smu:
                self.logger.error("No connection to instrument")
                return False, "No connection to instrument"

            # Log the command being sent
            self.logger.debug(f"Sending command: {command}")

            # Send the command
            self.smu.write(command)

            # Check for errors if enabled
            if check_errors:
                error = self.get_error()
                if error:
                    self.logger.error(f"Command error: {error}")
                    return False, error

            # Command successful
            self.logger.debug("Command executed successfully")
            return True, None

        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg