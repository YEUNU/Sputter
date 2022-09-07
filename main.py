import sys
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *   # pyqtSignal, QTimer
import serial
from keypad_dialog import keypadClass
import pyqtgraph as pg
import datetime
import csv
import time

main_uiFile = 'main_WXGA.ui'

def check_port():
    global real_port
    port_list = ["/dev/ttyACM0","/dev/ttyUSB1","COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9","COM10","COM11"]
    for i in range((len(port_list))):
        try:
            ser = serial.Serial(port = port_list[i], baudrate = 115200)
            real_port = port_list[i]
            print(real_port)
        except:
            print("failed")
check_port()

ser = serial.Serial(
    port = real_port,
    baudrate = 115200,
    timeout = 0.05
)

class read(QThread): # QThread, emit : https://ybworld.tistory.com/110 , https://wikidocs.net/71014
    send_chamber = pyqtSignal(int) # https://wikidocs.net/70990
    send_loadlock = pyqtSignal(int)
    send_temp = pyqtSignal(int)
    send_error = pyqtSignal(str)
    
    send_water = pyqtSignal(int)
    send_air = pyqtSignal(int)
    send_emergency = pyqtSignal(int)
    send_gas = pyqtSignal(int)
    send_motor = pyqtSignal(int)
    working = True

    def run(self):
        while self.working:
            try:
                chamber ='\x0501RSS0106%MW' + '210' +'\x04'    # \x05 : ENQ , \x04 : EOT
                chamber = chamber.encode()
                ser.write(chamber)
                chamber_read_v = ser.readline().decode('ascii')
                chamber_read = int(chamber_read_v[-5:-1], 16)
            except:
                self.send_error.emit('read')
                print('chamber error')
                
            try:
                loadlock ='\x0501RSS0106%MW' + '211' +'\x04'
                loadlock = loadlock.encode()
                ser.write(loadlock)
                loadlock_read_v = ser.readline().decode('ascii')
                loadlock_read = int(loadlock_read_v[-5:-1], 16)
            except:
                self.send_error.emit('read')
                print('loadlock error')

            try:
                temp ='\x0501RSS0106%MW' + '212' +'\x04'
                temp = temp.encode()
                ser.write(temp)
                temp_read_v = ser.readline().decode('ascii')
                temp_read = int(temp_read_v[-5:-1], 16)
            except:
                self.send_error.emit('read')
                print('temp error')
            
            try:
                water = '\x0501RSS0106%MW' + '213' + '\x04'
                water = water.encode()
                ser.write(water)
                water_read_v = ser.readline().decode('ascii')
                water_read = int(water_read_v[-5:-1], 16)
            except:
                self.send_error.emit('read')
                print('water error')

            try:
                air = '\x0501RSS0106%MW' + '214' + '\x04'
                air = air.encode()
                ser.write(air)
                air_read_v = ser.readline().decode('ascii')
                air_read = int(air_read_v[-5:-1], 16)
            except:
                self.send_error.emit('read')
                print('air error')

            try:
                emergency = '\x0501RSS0106%MW' + '215' + '\x04'
                emergency = emergency.encode()
                ser.write(emergency)
                emergency_read_v = ser.readline().decode('ascii')
                emergency_read = int(emergency_read_v[-5:-1], 16)
            except:
                self.send_error.emit('read')
                print('emergency error')

            try:
                gas = '\x0501RSS0106%MW' + '216' + '\x04'
                gas = gas.encode()
                ser.write(gas)
                gas_read_v = ser.readline().decode('ascii')
                gas_read = int(gas_read_v[-5:-1], 16)
            except:
                self.send_error.emit('read')
                print('gas error')
            
            try:
                motor = '\x0501RSS0106%MW' + '217' + '\x04'
                motor = motor.encode()
                ser.write(motor)
                motor_read_v = ser.readline().decode('ascii')
                motor_read = int(motor_read_v[-5:-1], 16)
            except:
                self.send_error.emit('read')
                print('motor error')

            if (
                (chamber_read_v[0] == '\x15') or (loadlock_read_v[0] == '\x15') or (temp_read_v[0] == '\x15')
            or (water_read_v[0] == '\x15') or (air_read_v[0] == '\x15') or (emergency_read_v[0] == '\x15')
            or (gas_read_v[0] == '\x15') or (motor_read_v[0] == '\x15')
            ):    # \x15 : NAK
                self.send_error.emit('read')
                break
                
            self.send_chamber.emit(chamber_read)
            self.send_loadlock.emit(loadlock_read)
            self.send_temp.emit(temp_read)

            self.send_water.emit(water_read)
            self.send_air.emit(air_read)
            self.send_emergency.emit(emergency_read)
            self.send_gas.emit(gas_read)
            self.send_motor.emit(motor_read)

            
class gui(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(main_uiFile, self)
        self.dig_list = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.anal_list = [0,0,0,0,0,0,0,0]
        self.x_count = 0
        self.xlist = list()
        self.chamber_vac_ylist = list()
        self.loadlock_vac_ylist = list()
        self.temp_ylist = list()
        self.set_temp_ylist = list()
        self.start_time = int()
        self.end_time = int()
        self.elapsed_time = int()
        self.log = str()
        self.log_list = list()
        self.timer = QTimer()
        self.water_v = int()
        self.air_v = int()
        self.emergency_v = int()
        self.gas_v = int()
        self.motor_status = int()
        self.run_status = False
        self.UIinit()
        self.UIstyle()
        ser.write(b'\x0501WSS0106%MW2040005\x04')
        QScroller.grabGesture(self.log_listview, QScroller.LeftMouseButtonGesture) # https://runebook.dev/ko/docs/qt/qscroller
        self.pen_blk = pg.mkPen(color=(0, 0, 0), width = 3) # https://pyqtgraph.readthedocs.io/en/latest/functions.html
        self.pen_grn = pg.mkPen(color=(0, 255, 0), width = 3)
        
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.elapsed)
        self.timer.start()
        
        self.worker = read()
        
        self.worker.send_chamber.connect(self.graph_chamber)
        self.worker.send_loadlock.connect(self.graph_loadlock)
        self.worker.send_temp.connect(self.graph_temp)
        self.worker.send_error.connect(self.error)
        
        self.worker.send_water.connect(self.water)
        self.worker.send_air.connect(self.air)
        self.worker.send_emergency.connect(self.emergency)
        self.worker.send_gas.connect(self.gas)
        self.worker.send_motor.connect(self.motor)
        self.worker.start()

        self.stop_clicked(1)

        # dig_list = [12f(0_ ), 12e(1_light), 12d(2_TMP_G/V), 12c(3_right_shutter), 12b(4_center_shutter), 12a(5_left_shutter), 129(6_shutter), 128(7_ ), 
        # 127(8_loadlock_Vent), 126(9_chamber_Vent), 125(10_Loadlock/V), 124(11_G/V), 123(12_F/V), 122(13_R/V), 121(14_TMP), 120(15_Rotary)]
        
        # anal = m200(GAS), m201(Temp), m202(Stagerotation), m203(T/V), m204(Sample_Load), m205(Lift), m206(left_run), m207(center_run), m208(right_run), m209(GAS_2)
        # anal_list = [m202(Stagerotation), m203(T/V), m204(Sample_Load-Linear_motor), m205(Lift), m206(left_run), m207(center_run), m208(right_run)]
    
        # read = m210(chamber_vac), m211(loadlock_vac), m212(temp), m213(water inlet), m214(air inlet), m215(emergency), m216(gas inlet), m217(motor_status)

    def elapsed(self):
        if self.run_status == True:
            self.end_time = time.time() # time, datetime : https://dojang.io/mod/page/view.php?id=2463 , https://mygumy.tistory.com/73
            elapsed_time = self.end_time - self.start_time
            result_list = str(datetime.timedelta(seconds = elapsed_time)).split(".")
            self.time_label.setText(result_list[0])

    def error(self, value):
        if value == 'read':
            QMessageBox.about(self, "FAIL", "DEVICE CONNECTION FAILED") # https://mr-doosun.tistory.com/29

    def plot_1(self, x_value, y_value, color):
        self.chamber_vac_graph.setBackground('w') # https://wikidocs.net/79452
        self.chamber_vac_graph.showGrid(x = True, y = True)
        if color == "blk":
            self.chamber_vac_graph.plot(x_value, y_value, pen = self.pen_blk)
        elif color == "grn":
            self.chamber_vac_graph.plot(x_value, y_value, pen = self.pen_grn)
    
    def plot_2(self, x_value, y_value, color):
        self.loadlock_vac_graph.setBackground('w')
        self.loadlock_vac_graph.showGrid(x = True, y = True)
        if color == "blk":
            self.loadlock_vac_graph.plot(x_value, y_value, pen = self.pen_blk)
        elif color == "grn":
            self.loadlock_vac_graph.plot(x_value, y_value, pen = self.pen_grn)
    
    def plot_3(self, x_value, y_value, color):
        self.temp_graph.setBackground('w')
        self.temp_graph.showGrid(x = True, y = True)
        if color == "blk":
            self.temp_graph.plot(x_value, y_value, pen = self.pen_blk)
        elif color == "grn":
            self.temp_graph.plot(x_value, y_value, pen = self.pen_grn)

    def graph_chamber(self, chamber):
        self.graph_Del()
        self.x_count += 1
        self.xlist.append(self.x_count)
        self.chamber_vac_ylist.append(chamber)
        self.plot_1(self.xlist, self.chamber_vac_ylist, 'blk')
        self.chamber_vac_label.setText(str(chamber))

    def graph_loadlock(self, loadlock):
        self.loadlock_vac_ylist.append(loadlock)
        self.plot_2(self.xlist, self.loadlock_vac_ylist, 'blk')
        self.loadlock_vac_label.setText(str(loadlock))

    def graph_temp(self, temp):
        self.temp_ylist.append(temp)        
        self.plot_3(self.xlist, self.temp_ylist, 'blk')
        self.now_temp_label.setText(str(temp))
        value = int(self.set_temp_input.text())
        if value > 0:
            for i in range(len(self.xlist)):
                self.set_temp_ylist.append(value)
            self.plot_3(self.xlist, self.set_temp_ylist, 'grn')
            self.set_temp_ylist = []

    def graph_Del(self):
        self.chamber_vac_graph.clear()
        self.loadlock_vac_graph.clear()
        self.temp_graph.clear()
        if len(self.xlist) >= 10:
            del self.xlist[0]
            del self.chamber_vac_ylist[0]
            del self.loadlock_vac_ylist[0]
            del self.temp_ylist[0]

    def water(self, water):
        self.water_v = water
        self.UIchange()

    def air(self, air):
        self.air_v = air
        self.UIchange()

    def emergency(self, emergency):
        self.emergency_v = emergency
        if self.emergency_v == 1:
            self.stop_clicked(0)

    def gas(self, gas):
        self.gas_v = gas
        self.UIchange()

    def motor(self, motor):
        self.motor_status = motor

    def rotary_clicked(self):
        if self.dig_list[15] == 1:
            self.dig_list[15] = 0
            self.log = 'Success Rotary Pump OFF'
            if self.dig_list[14] == 1:
                self.dig_list[15] = 1
                self.log = 'Failed Rotary Pump OFF'
                QMessageBox.about(self, "FAIL", self.log)
        elif self.dig_list[15] == 0:
            self.dig_list[15] = 1
            self.log = 'Success Rotary Pump ON'
        self.LOG()
        self.dig_send()

    def tmp_clicked(self):
        if self.dig_list[15] == 0:
            self.dig_list[14] = 0
            self.log = 'Failed TMP ON'
            QMessageBox.about(self, "FAIL", self.log)
        if self.dig_list[15] == 1:
            if self.dig_list[14] == 1:
                self.dig_list[14] = 0
                self.log = 'Success TMP OFF'
            elif self.dig_list[14] == 0:
                self.dig_list[14] = 1
                self.log = 'Success TMP ON'
        self.LOG()
        self.dig_send()

    def rotaryroughvalve_clicked(self):
        if self.dig_list[13] == 1:
            self.dig_list[13] = 0
            self.forelinevalve_button.show()
            self.log = 'Success Rotary Valve OFF'
        elif self.dig_list[13] == 0:
            self.dig_list[13] = 1
            self.forelinevalve_button.hide()
            self.log = 'Success Rotary Valve ON'
        self.LOG()
        self.dig_send()

    def forelinevalve_clicked(self):
        if self.dig_list[12] == 1:
            self.dig_list[12] = 0
            self.rotaryroughvalve_button.show()
            self.log = 'Success Foreline Valve OFF'
        elif self.dig_list[12] == 0:
            self.dig_list[12] = 1
            self.rotaryroughvalve_button.hide()
            self.log = 'Success Foreline Valve ON'
        self.LOG()
        self.dig_send()

    def gatevalve_clicked(self):
        if self.dig_list[11] == 1:
            self.dig_list[11] = 0
            self.log = 'Success Gate Valve OFF'
        elif self.dig_list[11] == 0:
            self.dig_list[11] = 1
            self.log = 'Success Gate Valve ON'
        if self.dig_list[8] == 1 or self.dig_list[9] == 1:
            self.dig_list[11] = 0
            self.log = 'Failed Gate Valve ON'
            QMessageBox.about(self, "FAIL", self.log)
        self.LOG()
        self.dig_send()

    def loadlockroughvalve_clicked(self):
        if self.dig_list[10] == 1:
            self.dig_list[10] = 0
            self.log = 'Success Loadlock Valve OFF'
        elif self.dig_list[10] == 0:
            self.dig_list[10] = 1
            self.log = 'Success Loadlock Valve ON'
        if self.dig_list[8] == 1:
            self.dig_list[10] = 0
            self.log = 'Failed Loadlock Valve ON'
            QMessageBox.about(self, "FAIL", self.log)
        self.LOG()
        self.dig_send()

    def chambervent_clicked(self):
        if self.dig_list[2] + self.dig_list[11] + self.dig_list[13] + self.anal_list[1] == 0: #
            if self.dig_list[9] == 1:
                self.dig_list[9] = 0
                self.log = 'Success Chamber Vent OFF'
            elif self.dig_list[9] == 0:
                self.dig_list[9] = 1
                self.log = 'Success Chamber Vent ON'
            self.dig_send()

        else:
            self.log = 'Failed Chamber Vent ON'
            QMessageBox.about(self, "FAIL", self.log)
        self.LOG()

    def loadlockvent_clicked(self):
        if self.dig_list[10] + self.dig_list[11] == 0:
            if self.dig_list[8] == 1:
                self.dig_list[8] = 0
                self.log = 'Success Loadlock Vent OFF'
            elif self.dig_list[8] == 0:
                self.dig_list[8] = 1
                self.log = 'Success Loadlock Vent ON'
            self.dig_send()
        else:
            self.log = 'Failed Loadlock Vent ON'
            QMessageBox.about(self, "FAIL", self.log)
        self.LOG()

    def shutter_clicked(self):
        if self.dig_list[6] == 1:
            self.dig_list[6] = 0
            self.log = 'Success Shutter OFF'
        elif self.dig_list[6] == 0:
            self.dig_list[6] = 1
            self.log = 'Success Shutter ON'
        self.LOG()
        self.dig_send()

    def leftshutter_clicked(self):
        if self.dig_list[5] == 1:
            self.dig_list[5] = 0
            self.log = 'Success Left Shutter OFF'
        elif self.dig_list[5] == 0:
            self.dig_list[5] = 1
            self.log = 'Success Left Shutter ON'
        self.LOG()
        self.dig_send()

    def centershutter_clicked(self):
        if self.dig_list[4] == 1:
            self.dig_list[4] = 0
            self.log = 'Success Center Shutter OFF'
        elif self.dig_list[4] == 0:
            self.dig_list[4] = 1
            self.log = 'Success Center Shutter ON'
        self.LOG()
        self.dig_send()

    def rightshutter_clicked(self):
        if self.dig_list[3] == 1:
            self.dig_list[3] = 0
            self.log = 'Success Right Shutter OFF'
        elif self.dig_list[3] == 0:
            self.dig_list[3] = 1
            self.log = 'Success Right Shutter ON'
        self.LOG()
        self.dig_send()

    def tmpgatevalve_clicked(self):
        if self.dig_list[2] == 1:
            self.dig_list[2] = 0
            self.log = 'Success TMP Gate Valve OFF'
        elif self.dig_list[2] == 0:
            self.dig_list[2] = 1
            self.log = 'Success TMP Gate Valve ON'
        if self.dig_list[9] == 1:
            self.dig_list[2] = 0
            self.log = 'Failed TMP Gate Valve ON'
            QMessageBox.about(self, "FAIL", self.log)
        self.LOG()
        self.dig_send()

    def light_clicked(self):
        if self.dig_list[1] == 1:
            self.dig_list[1] = 0
            self.log = 'Success Light OFF'
        elif self.dig_list[1] == 0:
            self.dig_list[1] = 1
            self.log = 'Success Light ON'
        self.LOG()
        self.dig_send()
        
    def keypad(self, button):
        try:
            dlg = keypadClass()
            r = dlg.showmodal()
            if r:
                text = dlg.keypad_val.text()
                if button == "gas1_input":
                    self.gas1_input.setText(text)
                    self.log = 'GAS1 ' + self.gas1_input.text() + ' SCCM set'
                    self.LOG()
                if button == "gas2_input":
                    self.gas2_input.setText(text)
                    self.log = 'GAS2 ' + self.gas2_input.text() + ' SCCM set'
                    self.LOG()
                if button == "set_temp_input": 
                    self.set_temp_input.setText(text)
                    self.temp_clicked()

        except:
            print("keypad error")

    def gas1_clicked(self):
        self.ans = (hex(int(self.gas1_input.text()))[2:]) # 10진수를 16진수로 변환 , https://infinitt.tistory.com/91
        self.log = 'GAS1 ON'
        self.LOG()
        self.anal_send(200)

    def gas2_clicked(self):
        self.ans = (hex(int(self.gas2_input.text()))[2:])
        self.log = 'GAS2 ON'
        self.LOG()
        self.anal_send(209)
        
    def temp_clicked(self):
        self.ans = (hex(int(self.set_temp_input.text()))[2:])
        self.log = self.set_temp_input.text() + '°C' + ' set'
        self.LOG()
        self.anal_send(201)

    def stagerotation_clicked(self):
        if self.anal_list[0] == 1:
            self.anal_list[0] = 0
            self.ans = 0
            self.log = 'Success Stage Rotation OFF'
        elif self.anal_list[0] == 0:
            self.anal_list[0] = 1
            self.ans = 1
            self.log = 'Success Stage Rotation ON'
        self.LOG()
        self.anal_send(202)
        
    def throttlevalve_clicked(self):
        if self.anal_list[1] == 1:
            self.anal_list[1] = 0
            self.ans = 0
            self.log = 'Success Throttle Valve OFF'
        elif self.anal_list[1] == 0:
            self.anal_list[1] = 1
            self.ans = 1
            self.log = 'Success Throttle Valve ON'
        if self.dig_list[9] == 1:
            self.anal_list[1] = 0
            self.log = 'Failed Throttle Valve ON'
            QMessageBox.about(self, "FAIL", self.log)
        self.LOG()
        self.anal_send(203)
        
    def sampleload_clicked(self):
        if self.motor_status == 0: # motor_status = 0 원점 설정중, motor_status = 1 이동중, motor_status = 2 이동 종료, 다음 동작 가능
            print(self.motor_status)
            self.anal_list[2] = 0
            self.log = 'Failed Sample Load Activate'
            QMessageBox.about(self, "FAIL", self.log)

        elif self.motor_status == 1:
            if self.anal_list[2] == 1:
                self.anal_list[2] = 1
            if self.anal_list[2] == 0:
                self.anal_list[2] = 0
            self.log = 'Failed Sample Load Activate'
            QMessageBox.about(self, "FAIL", self.log)

        elif self.motor_status == 2:
            if self.anal_list[2] == 1:
                self.anal_list[2] = 0
                self.ans = 0
                self.log = 'Success Sample Load OFF'
                
            elif self.anal_list[2] == 0:
                self.anal_list[2] = 1
                self.ans = 1
                self.log = 'Success Sample Load ON'
            self.anal_send(204)
            time.sleep(1)

        self.LOG()
        
    def lift_clicked(self):
        if self.anal_list[3] == 1:
            self.anal_list[3] = 0
            self.ans = 0
            self.log = 'Success Lift OFF'
        elif self.anal_list[3] == 0:
            self.anal_list[3] = 1
            self.ans = 1
            self.log = 'Success Lift ON'
        self.LOG()
        self.anal_send(205)

    def leftrun_clicked(self):
        if self.run_status == False:
            self.start_time = time.time()
            self.run_status = True

        if self.anal_list[4] == 1:
            self.anal_list[4] = 0
            self.ans = 0
            self.log = 'Success Left Run OFF'
        elif self.anal_list[4] == 0:
            self.anal_list[4] = 1
            self.ans = 1
            self.log = 'Success Left Run ON'
        self.LOG()
        self.anal_send(206)

        if self.anal_list[4] + self.anal_list[5] + self.anal_list[6] == 0 and self.run_status == True:
            self.end_time = time.time()
            self.run_status = False
    
    def centerrun_clicked(self):
        if self.run_status == False:
            self.start_time = time.time()
            self.run_status = True

        if self.anal_list[5] == 1:
            self.anal_list[5] = 0
            self.ans = 0
            self.log = 'Success Center Run OFF'
        elif self.anal_list[5] == 0:
            self.anal_list[5] = 1
            self.ans = 1
            self.log = 'Success Center Run ON'
        self.LOG()
        self.anal_send(207)
        
        if self.anal_list[4] + self.anal_list[5] + self.anal_list[6] == 0 and self.run_status == True:
            self.end_time = time.time()
            self.run_status = False
    
    def rightrun_clicked(self):
        if self.run_status == False:
            self.start_time = time.time()
            self.run_status = True

        if self.anal_list[6] == 1:
            self.anal_list[6] = 0
            self.ans = 0
            self.log = 'Success Right run OFF'
        elif self.anal_list[6] == 0:
            self.anal_list[6] = 1
            self.ans = 1
            self.log = 'Success Right Run ON'
        self.LOG()
        self.anal_send(208)

        if self.anal_list[4] + self.anal_list[5] + self.anal_list[6] == 0 and self.run_status == True:
            self.end_time = time.time()
            self.run_status = False

    def rotatelight_clicked(self):
        if self.anal_list[7] == 1:
            self.anal_list[7] = 0
            self.ans = 0
            self.log = 'Success Rotate Light OFF'
        elif self.anal_list[7] == 0:
            self.anal_list[7] = 1
            self.ans = 1
            self.log = 'Success Rotate Light ON'
        self.LOG()
        self.anal_send(217)

    def stop_clicked(self, num):
        self.dig_list = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.anal_list = [0,0,0,0,0,0,0,0]
        self.ans = 0
        self.x_count = 0
        self.xlist = []
        self.chamber_vac_ylist = []
        self.loadlock_vac_ylist = []
        self.temp_ylist = []
        self.set_temp_input.setText('0')
        self.gas1_input.setText('0')
        self.gas2_input.setText('0')
        self.graph_Del()
        self.dig_send()
        self.anal_send('stop')
        self.worker.start()
        if num != 1:
            self.log = 'Success Emergency Stop'
            self.LOG()

    def dig_send(self):
        self.worker.working = False
        time.sleep(0.6)
        b_str = str()
        for i in range(len(self.dig_list)):
            b_str = b_str + str(self.dig_list[i])
        int_str = int(b_str,2) # 2진수를 10진수로 변환
        ans = (hex(int_str)[2:]) # 10진수를 16진수로 변환
        ans = '{:0>4}'.format(ans) # https://wikidocs.net/13

        self.input ='\x0501WSS0106%PW012'+ ans +'\x04' # 트랜지스터 03 번째 tn32a로 변경함 pw012(방)
        
        self.input = self.input.encode()
        ser.write(self.input)
        time.sleep(0.5)
        self.UIchange()
        self.worker.working = True
        self.worker.start()

    def anal_send(self, adress):
        self.worker.working = False
        time.sleep(0.6)
        self.ans = '{:0>4}'.format(self.ans)
        if adress == 'stop':
            for i in range(200, 210):
                if i != 204:
                    adress = i
                    self.input ='\x0501WSS0106%MW' + str(adress) + str(self.ans) +'\x04'
                    self.input = self.input.encode()
                    ser.write(self.input)
                    time.sleep(0.3)

        else:
            self.input ='\x0501WSS0106%MW' + str(adress) + str(self.ans) +'\x04'
            self.input = self.input.encode()
            ser.write(self.input)
            time.sleep(0.5)
        self.UIchange()
        self.worker.working = True
        self.worker.start()
        

    def LOG(self):
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S ')
        self.log = nowDatetime + self.log
        self.log_listview.addItem(self.log)
        
        self.log_csv = self.log.replace(' ', ',', 2).split(',')
        self.log_list.append(self.log_csv)

    def save_clicked(self):
        now = datetime.datetime.now()
        nowDatetime = str(now.strftime('%Y-%m-%d %H.%M.%S')+'.csv')
        
        f = open(nowDatetime, 'w', newline = '') # https://devpouch.tistory.com/55
        wr = csv.writer(f)
        for i in range(0, len(self.log_list)):
            wr.writerow(self.log_list[i])
        f.close()

    def delete_clicked(self):
        self.log_list = []
        self.log_listview.clear()

    def change_page(self, num):
        self.stackedWidget.setCurrentIndex(num)

    def closeEvent(self):
        reply = QMessageBox.question(self, 'Message',
            "Exit the program", QMessageBox.Yes | QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            sys.exit()

    def UIinit(self):
        self.power_button.clicked.connect(self.closeEvent)

        self.rotary_button.clicked.connect(self.rotary_clicked)
        self.tmp_button.clicked.connect(self.tmp_clicked)
        self.rotaryroughvalve_button.clicked.connect(self.rotaryroughvalve_clicked)
        self.forelinevalve_button.clicked.connect(self.forelinevalve_clicked)
        self.gatevalve_button.clicked.connect(self.gatevalve_clicked)
        self.loadlockroughvalve_button.clicked.connect(self.loadlockroughvalve_clicked)
        self.chambervent_button.clicked.connect(self.chambervent_clicked)
        self.loadlockvent_button.clicked.connect(self.loadlockvent_clicked)
        self.shutter_button.clicked.connect(self.shutter_clicked)
        self.leftshutter_button.clicked.connect(self.leftshutter_clicked)
        self.centershutter_button.clicked.connect(self.centershutter_clicked)
        self.rightshutter_button.clicked.connect(self.rightshutter_clicked)
        self.tmpgatevalve_button.clicked.connect(self.tmpgatevalve_clicked)
        self.light_button.clicked.connect(self.light_clicked)

        self.gas1_button.clicked.connect(self.gas1_clicked)
        self.gas2_button.clicked.connect(self.gas2_clicked)
        self.stagerotation_button.clicked.connect(self.stagerotation_clicked)
        self.throttlevalve_button.clicked.connect(self.throttlevalve_clicked)
        self.sampleload_button.clicked.connect(self.sampleload_clicked)
        self.lift_button.clicked.connect(self.lift_clicked)
        self.leftrun_button.clicked.connect(self.leftrun_clicked)
        self.centerrun_button.clicked.connect(self.centerrun_clicked)
        self.rightrun_button.clicked.connect(self.rightrun_clicked)
        self.stop_button.clicked.connect(lambda:self.stop_clicked(0))
        self.logsave_button.clicked.connect(self.save_clicked)
        self.delete_button.clicked.connect(self.delete_clicked)

        self.gas1_input.clicked.connect(lambda:self.keypad("gas1_input"))
        self.gas2_input.clicked.connect(lambda:self.keypad("gas2_input"))
        self.set_temp_input.clicked.connect(lambda:self.keypad("set_temp_input"))

        self.main_button.clicked.connect(lambda:self.change_page(0))
        self.chamber_button.clicked.connect(lambda:self.change_page(1))
        self.chamber2_button.clicked.connect(lambda:self.change_page(1))
        self.loadlock_button.clicked.connect(lambda:self.change_page(1))
        self.graph_button.clicked.connect(lambda:self.change_page(2))
        self.log_button.clicked.connect(lambda:self.change_page(3))
        
    def UIchange(self):
        self.UIstyle()
        if self.dig_list[15] == 1:
            self.rotary_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.dig_list[14] == 1:
            self.tmp_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.dig_list[13] == 1:
            self.rotaryroughvalve_button.setStyleSheet(
                '''
                QPushButton{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
            self.line_10.setStyleSheet(
                '''
                border-style:solid; border-color:rgb(3, 200, 3);
                '''
                )
            self.line_11.setStyleSheet(
                '''
                border-style:solid; border-color:rgb(3, 200, 3);
                '''
                )
            self.line_13.setStyleSheet(
                '''
                border-style:solid; border-color:rgb(3, 200, 3);
                '''
                )
        if self.dig_list[12] == 1:
            self.forelinevalve_button.setStyleSheet(
                '''
                QPushButton{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
            self.line_5.setStyleSheet(
                '''
                border-style:solid; border-color:rgb(3, 200, 3);
                '''
                )
        if self.dig_list[11] == 1:
            self.gatevalve_button.setStyleSheet(
                '''
                QPushButton{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
            self.line_6.setStyleSheet(
                '''
                border-style:solid; border-color:rgb(3, 200, 3);
                '''
                )
        if self.dig_list[10] == 1:
            self.loadlockroughvalve_button.setStyleSheet(
                '''
                QPushButton{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
            self.line.setStyleSheet(
                '''
                border-style:solid; border-color:rgb(3, 200, 3);
                '''
                )
            self.line_4.setStyleSheet(
                '''
                border-style:solid; border-color:rgb(3, 200, 3);
                '''
                )
        if self.dig_list[9] == 1:
            self.chambervent_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.dig_list[8] == 1:
            self.loadlockvent_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.dig_list[6] == 1:
            self.shutter_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.dig_list[5] == 1:
            self.leftshutter_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(100, 200, 3); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.dig_list[4] == 1:
            self.centershutter_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(100, 200, 3); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.dig_list[3] == 1:
            self.rightshutter_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(100, 200, 3); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.dig_list[2] == 1:
            self.tmpgatevalve_button.setStyleSheet(
                '''
                QPushButton{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
            self.line_8.setStyleSheet(
                '''
                border-style:solid; border-color:rgb(3, 200, 3);
                '''
                )
        if self.dig_list[1] == 1:
            self.light_button.setStyleSheet(
                '''
                QPushButton{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.anal_list[0] == 1:
            self.stagerotation_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.anal_list[1] == 1:
            self.throttlevalve_button.setStyleSheet(
                '''
                QPushButton{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.anal_list[2] == 1:
            self.sampleload_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.anal_list[3] == 1:
            self.lift_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(86, 3, 161); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        if self.anal_list[4] == 1:
            self.leftrun_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(200, 3, 3); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )

        if self.anal_list[5] == 1:
            self.centerrun_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(200, 3, 3); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        
        if self.anal_list[6] == 1:
            self.rightrun_button.setStyleSheet(
                '''
                QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(200, 3, 3); color: rgb(255,255,255);}
                QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
                '''
                )
        
        if self.water_v == 1:
            self.waterinlet_label.setStyleSheet(
                '''
                QLabel{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(0,0,0); color: rgb(255, 255, 255);}
                '''
                )
        
        if self.air_v == 1:
            self.airinlet_label.setStyleSheet(
                '''
                QLabel{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(0,0,0); color: rgb(255, 255, 255);}
                '''
                )
        # if self.emegency_v == 1:

        if self.gas_v == 1:
            self.gasinlet_label.setStyleSheet(
                '''
                QLabel{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(0,0,0); color: rgb(255, 255, 255);}
                '''
                )

    def UIstyle(self):
        self.power_button.setStyleSheet(
            '''
            QPushButton{border:0px; image:url(./pic/power.png); background-color: rgb(3, 86, 161);}
            QPushButton:pressed{border:2px; background-color: rgb(3, 86, 130);}
            '''
        )
        self.rotary_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.tmp_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        
        self.rotaryroughvalve_button.setStyleSheet(
            '''
            QPushButton{font: 16pt "Arial"; border-style: solid; border-width: 1px; border-radius: 6px; border-color: rgb(3, 86, 161); background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )

        self.line_10.setStyleSheet(
            '''
            border-style:solid; border-color:rgb(0, 0, 0);
            '''
            )
        self.line_11.setStyleSheet(
            '''
            border-style:solid; border-color:rgb(0, 0, 0);
            '''
            )
        self.line_13.setStyleSheet(
            '''
            border-style:solid; border-color:rgb(0, 0, 0);
            '''
            )

        self.forelinevalve_button.setStyleSheet(
            '''
            QPushButton{font: 16pt "Arial"; border-style: solid; border-width: 1px; border-radius: 6px; border-color: rgb(3, 86, 161); background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )

        self.line_5.setStyleSheet(
            '''
            border-style:solid; border-color:rgb(0, 0, 0);
            '''
            )
        self.gatevalve_button.setStyleSheet(
            '''
            QPushButton{font: 16pt "Arial"; border-style: solid; border-width: 1px; border-radius: 6px; border-color: rgb(3, 86, 161); background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.line_6.setStyleSheet(
            '''
            border-style:solid; border-color:rgb(0, 0, 0);
            '''
            )
        self.loadlockroughvalve_button.setStyleSheet(
            '''
            QPushButton{font: 16pt "Arial"; border-style: solid; border-width: 1px; border-radius: 6px; border-color: rgb(3, 86, 161); background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.line.setStyleSheet(
            '''
            border-style:solid; border-color:rgb(0, 0, 0);
            '''
            )
        self.line_4.setStyleSheet(
            '''
            border-style:solid; border-color:rgb(0, 0, 0);
            '''
            )
        self.chambervent_button.setStyleSheet(
            '''
            QPushButton{border-style: solid; border-width: 2px; border-radius: 10px; border-color: rgb(255, 255, 255); background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.loadlockvent_button.setStyleSheet(
            '''
            QPushButton{border-style: solid; border-width: 2px; border-radius: 10px; border-color: rgb(255, 255, 255); background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.shutter_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.leftshutter_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(200, 100, 3); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.centershutter_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(200, 100, 3); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.rightshutter_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(200, 100, 3); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.tmpgatevalve_button.setStyleSheet(
            '''
            QPushButton{font: 16pt "Arial"; border-style: solid; border-width: 1px; border-radius: 6px; border-color: rgb(3, 86, 161); background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.line_8.setStyleSheet(
            '''
            border-style:solid; border-color:rgb(0, 0, 0);
            '''
            )
        self.light_button.setStyleSheet(
            '''
            QPushButton{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.stagerotation_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.throttlevalve_button.setStyleSheet(
            '''
            QPushButton{font: 16pt "Arial"; border-style: solid; border-width: 1px; border-radius: 6px; border-color: rgb(3, 86, 161); background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.sampleload_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.lift_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 86, 161); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.leftrun_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 200, 3); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.centerrun_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 200, 3); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )
        self.rightrun_button.setStyleSheet(
            '''
            QPushButton{border-width: 2px; border-radius: 10px; background-color: rgb(3, 200, 3); color: rgb(255,255,255);}
            QPushButton:pressed{border-width: 2px; border-radius: 10px; background-color: rgb(180 , 180, 180); color: rgb(0,0,0); }
            '''
            )

        self.waterinlet_label.setStyleSheet(
                '''
                QLabel{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
                '''
                )

        self.airinlet_label.setStyleSheet(
                '''
                QLabel{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
                '''
                )

        self.gasinlet_label.setStyleSheet(
                '''
                QLabel{font: 16pt "Arial"; border-width: 2px; border-radius: 10px; background-color: rgb(255, 255, 255); color: rgb(0,0,0);}
                '''
                )

        self.logo_label.setPixmap(QPixmap("./pic/tera.png"))
        

app = QApplication(sys.argv)
myWindow = gui() 
# myWindow.show()
myWindow.showFullScreen()
sys.exit(app.exec_())