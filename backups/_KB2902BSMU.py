# The program for Keysight B2902B SMU
# The program functions are:
# 1. connect or disconnect to the SMU
# 2. set the voltage or current for channel 1 and/or 2
# 3. turn on/off the output for channel 1 and/or 2

import pyvisa


class ksb2902bsmu:
    def __init__(self):
        return

    def connect(self):
        self.rm = pyvisa.ResourceManager()
        self.visaport = 'USB0::0x0957::0x8C18::MY51141244::0::INSTR'
        self.smu = self.rm.open_resource(self.visaport, timeout=10000)
        if self.smu:
            print('Connect')

        self.smu.write(":syst:beep:stat on")

    # 發出beep警示聲
    def beep(self):
        self.smu.write("syst:beep 440,0.5")

    # 讀取是否有錯誤
    def systerr(self):
        self.smu.write(':syst:err:all?')
        self.textBrowser_errormessage.append(self.smu.read())

    # 設定讀取電流的上限
    def set_compliance(self):
        self.smu.write(":SENS1:FUNC:ALL")
        self.smu.write(":SENS2:FUNC:ALL")
        self.smu.write(":SENS1:CURR:PROT " + self.lineEdit_compliance.text())
        self.smu.write(":SENS2:CURR:PROT " + self.lineEdit_compliance.text())

    # 開啟通道
    def output_on(self, channel):
        self.smu.write((":outp" + channel + " on"))
        self.systerr()

        if int(self.smu.query("outp" + channel + '?')):
            self.textBrowser_errormessage.append('channel' + channel + ' On')
            self.systerr()
        else:
            self.textBrowser_errormessage.append(
                '!!!channel' + channel + ' On failed!!!')
            self.systerr()

    # 關掉通道
    def output_off(self, channel):
        self.smu.write(":outp" + channel + ' off')
        self.systerr()

        if not int(self.smu.query("outp" + channel + '?')):
            self.textBrowser_errormessage.append('channel' + channel + ' Off')
        else:
            self.textBrowser_errormessage.append(
                '!!!channel' + channel + ' Off failed!!!')

    # 設定電壓
    def set_output_volt(self, channel, volt):
        self.smu.write(":sour" + channel + ":func:mode volt")
        self.smu.write(":sour" + channel + ":volt:rang:auto on")
        self.smu.write(":sour" + channel + ":volt " + volt)
        self.beep()
        self.systerr()

    # 執行量測電壓、電流與電阻
    def measurement(self, channel):

        meas_volt = self.smu.query(":meas:volt? (@" + channel + ")")
        meas_curr = self.smu.query(":meas:curr? (@" + channel + ")")
        meas_res = self.smu.query(":meas:res? (@" + channel + ")")

        self.beep()
        self.systerr()

        # self.smu.write('*RST')
        # self.smu.write(':SOUR1:FUNC:MODE VOLT')
        # self.smu.write(':SOUR2:FUNC:MODE VOLT')
        # self.smu.write(':SOUR1:VOLT:RANG 1')
        # self.smu.write(':SOUR2:VOLT:RANG 1')
        # self.smu.write(':SOUR1:VOLT 0')
        # self.smu.write(':SOUR2:VOLT 0')
        # self.smu.write(':OUTP1 OFF')
        # self.smu.write(':OUTP2 OFF')
        # self.smu.write(':SENS1:FUNC:CONC OFF')
        # self.smu.write(':SENS2:FUNC:CONC OFF')
        # self.smu.write(':SENS1:FUNC "CURR"')
        # self.smu.write(':SENS2:FUNC "CURR"')
        # self.smu.write(':SENS1:CURR:PROT 1e-3')
        # self.smu.write(':SENS2:CURR:PROT 1e-3')
        # self.smu.write(':SENS1:CURR:RANG 1e-3')
        # self.smu.write(':SENS2:CURR:RANG 1e-3')
        # self.smu.write(':SENS1:CURR:NPLC 1')
        # self.smu.write(':SENS2:CURR:NPLC 1')
        # self.smu.write(':FORM:ELEM CURR')
        # self.smu.write(':FORM:ELEM VOLT')
        # self.smu.write(':FORM:ELEM TIME')
        # self.smu.write(':FORM:ELEM READ')
        # self.smu.write(':TRIG:COUN 1')
        # self.smu.write(':TRIG:DEL 0')
        # self.smu.write(':TRIG:SOUR TIM')
        # self.smu.write(':TRIG:TIM 0.01')
        # self.smu.write(':TRIG:BLOC:BUFF:CLE')
        # self.smu.write(':TRIG:BLOC:BUFF:CLE')
        # self.smu.write(':TRIG:BLOC:BUFF:CLE')


