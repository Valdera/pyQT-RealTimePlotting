from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys
from serial import Serial
import serial
import platform
import time
from ui_main import Ui_MainWindow
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from worker import Worker
import numpy as np
import pyrebase

flagTime = 0
flagHiddenGraph = False
flagThread = True
delayTime = 0.05

# TODO : 
# DONE CHANGE ARRAY TO NUMPY ARRAY 
# DONE IMPLEMENT HIDDEN LINE
# DONE FIX HEIGHT ADJUST
# DONE REGION OF INTEREST
# DONE SET RANGE IN MINI GRAPH
# DONE MAKE LOGIN UI
# DONE MAKE DATA TRANSFORMATION ARCHITECTURE
# DONE CONFIGURE WITH FIREBASE
# DONE CRUD OPERATIONS
# DONE DATABASE PAGE
# DONE SETTING PAGE
# DONE ERROR HANDLING


def serial_ports():
    '''
    Get all the active port in the computer
    '''
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def connect_port(port):
    '''
    Connect to the port
    '''
    serialPort = serial.Serial(port = port, baudrate=9600, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    return serialPort

def initButton(self):
    '''
    Init all the button required
    '''
    self.btn_page_1.clicked.connect(self.trackerButton)
    self.btn_page_2.clicked.connect(self.databaseButton)
    # self.btn_page_3.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_3))
    self.refreshButton.pressed.connect(lambda: self.refreshClick())
    self.startButton1.pressed.connect(lambda: self.execute_thread())
    self.stopButton1.pressed.connect(lambda: self.stopThreading())
    # self.createButton.pressed.connect(lambda: self.changePage(0))
    self.graphRightButton.pressed.connect(lambda: self.switchMiniGraph('R'))
    self.graphLeftButton.pressed.connect(lambda: self.switchMiniGraph('L'))
    self.loginButton.pressed.connect(lambda: self.login())
    self.toCreateButton.pressed.connect(lambda: self.changePage(2))
    self.createButton.pressed.connect(lambda: self.create())
    self.createAgeEdit.textEdited.connect(self.create_age)
    self.createIdEdit.textEdited.connect(self.create_id)
    self.createNameEdit.textEdited.connect(self.create_name)
    self.loginIdEdit.textEdited.connect(self.login_id)
    self.comboGenderBox.currentIndexChanged[str].connect(self.create_gender)
    self.saveButton.pressed.connect(lambda: self.save())


def initGraph(self):
    '''
    Init the main graph
    '''
    # Plot the graph
    pen_region = pg.mkPen(color='#F59100', width=2)
    brush = pg.mkBrush(color='#F5910020')
    self.graphWidget = pg.PlotWidget()
    self.region = pg.LinearRegionItem([0,0], movable=False, orientation='horizontal', brush=brush)
    self.region.setZValue(-10)
    self.graphWidget.addItem(self.region)
    # self.graphWidget.ROI([20, 20], [20, 20], pen=(0,9))
    
    # GUI Configuration
    self.graphWidget.setBackground('w')
    self.graphWidget.setTitle("Main Graph", color="#F59100", size="13pt")
    #00F794
    styles = {"color": "#F59100", "font-size": "20px"}
    self.graphWidget.setLabel("left", "Range (mm)", **styles)
    self.graphWidget.setLabel("bottom", "Seconds (s)", **styles)
    pen = pg.mkPen(color='#F59100', width=2)
    hiddenpen = pg.mkPen(color='#EA020B', width=2)
    
    # Set the data for the graph
    self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)
    self.hidden_line = self.graphWidget.plot(self.x, self.hidden, connect="finite", pen=hiddenpen)
    
    # Graph Range
    self.graphWidget.setXRange(self.xRange, self.xRange+50, padding=0)
    self.graphWidget.showGrid(x=True, y=True)

def initMiniGraph(self):
    '''
    Init the mini graph
    '''
    # Plot the graph
    self.miniGraphWidget = pg.PlotWidget()
    
    # UI Configuration
    self.miniGraphWidget.setBackground('w')
    self.miniGraphWidget.setTitle("Graph for sensor A", color="#F59100", size="10pt")
    styles = {"color": "#F59100", "font-size": "13px"}
    self.miniGraphWidget.setLabel("left", "Range (mm)", **styles)
    self.miniGraphWidget.setLabel("bottom", "Seconds (s)", **styles)
    pen = pg.mkPen(color='#F59100', width=2)
    
    # Set the data for the graph
    self.mini_data_line =  self.miniGraphWidget.plot(self.x, self.sensorA, pen=pen)

    # Graph Range
    self.miniGraphWidget.setXRange(self.xRange, self.xRange+50, padding=0)
    self.miniGraphWidget.showGrid(x=True, y=True)


def filterInput(i):
    try:
        stringArr = str(i)[2:].split(";")[:-1]
        if (stringArr[0][:1] == "\\"):
            stringArr[0] = 0
        arr = [int(i) for i in stringArr]
        return arr
    except IndexError:
        return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    except ValueError:
        return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

 
def messageError(title, message):
    msg = QMessageBox()
    msg.setText(message)
    # msg.setInformativeText('More information')
    msg.setWindowTitle(title)
    msg.exec_()

class MainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self, *args, obj=None,**kwargs):
        '''
        Init class
        '''
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.threadpool = QThreadPool()
        self.stackedWidgetMain.setCurrentIndex(1)
        self.stackedWidget.setCurrentWidget(self.page_1)
        # Patient Variables
        self.createPatientName = ""
        self.createPatientAge = 0
        self.createPatientId = ""
        self.createPatientGender = "Male"

        self.loginPatientId = ""

        # Patient Variables
        self.currentPatient = {}

        self.currentMax = 0
        self.currentMin = 0
        self.currentRate = 0
        self.total = 0

        initButton(self)
        # Make the stop button invisible
        self.stopButton1.setHidden(True)

        # Get all serial ports currently connected
        self.curr_working = False
        self.serialPorts = serial_ports()
        self.comboBoxArd.addItems(self.serialPorts)
        self.currentPort = ''
        self.currentPortName = self.serialPorts[0]
        self.comboBoxArd.currentIndexChanged[str].connect(self.port_changed)

        # Main Graph Value
        self.x = np.array([0])  
        self.y = np.array([0])  
        self.hidden_x = np.array([0])
        self.hidden = np.array([0])
        self.seconds = np.array([0])
        self.xRange = 0

        # Mini Graph Value
        self.sensorA = np.array([0])
        self.sensorB = np.array([0])
        self.sensorC = np.array([0])
        self.sensorD = np.array([0])
        self.sensorE = np.array([0])
        self.sensorF = np.array([0])
        self.sensorG = np.array([0])
        self.sensorH = np.array([0])
        self.sensorI = np.array([0])
        self.currentMiniY = 'A'

        # Graph init
        graphLayout = QVBoxLayout()
        initGraph(self)
        graphLayout.addWidget(self.graphWidget)

        # Mini GraphInit
        miniGraphLayout = QVBoxLayout()
        initMiniGraph(self)
        miniGraphLayout.addWidget(self.miniGraphWidget)

        # Insert Layout
        self.frameGraphMain.setLayout(graphLayout)
        self.frameGraphMini.setLayout(miniGraphLayout)

        # Firebase 
        # self.firebase = firebase.FirebaseApplication('https://pythonrscm-default-rtdb.firebaseio.com/', None)  
        firebaseConfig =  {
            "apiKey": "AIzaSyCU_voEKdNpWbqxR8xJJLbEcVqkMIR6TBY",
            "authDomain": "pythonrscm.firebaseapp.com",
            "databaseURL": "https://pythonrscm-default-rtdb.firebaseio.com",
            "projectId": "pythonrscm",
            "storageBucket": "pythonrscm.appspot.com",
            "messagingSenderId": "613770294252",
            "appId": "1:613770294252:web:04696f4426ed13eab386c9",
            "measurementId": "G-JFQ69FT00H"
        }

        try:
            firebase = pyrebase.initialize_app(firebaseConfig)
            self.db=firebase.database()
        except:
            messageError('Error', 'Error connecting to database. Please connect to internet')



    def stopThreading(self):
        '''
        The function to stop the thread
        '''
        Worker.flagThread = False
        self.currentPort.close()

    def execute_this_fn(self):
        '''
        The function to be executed when the thread runs
        '''
        # try:
        global delayTime
        line = self.currentPort.readline()
        filtered = filterInput(line)
        time.sleep(delayTime)
        return filtered
            # except TypeError:
            #     messageError('Error', 'Please restart the app and reconnect the device')
            # except serial.serialutil.PortNotOpenError:
            #     return 
        # except serial.serialutil.SerialException:
        #     return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            # messageError('Error', 'Please restart the app and reconnect the device')

    def thread_complete(self):
        '''
        This function run after thread finished
        '''
        self.curr_working = False
        self.startButton1.setHidden(False)
        # self.stopButton1.setHidden(True)
        Worker.flagThread = True        
        # self.currentPort.close()
        print("THREAD COMPLETE")
    
    def result_process(self, new_y):
        '''
        Getting the result from the output
        '''
        self.update_plot_graph(new_y)

    def execute_thread(self):
        '''
        Execute the thread
        '''
        self.curr_working = True
        self.startButton1.setHidden(True)
        # self.stopButton1.setHidden(False)
        self.currentPort = connect_port(self.currentPortName)
        worker = Worker(self.execute_this_fn) 
        worker.signals.result.connect(self.result_process)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)

    def closeEvent(self, event):
        '''
        Close all thread before quit
        '''
        Worker.flagThread = False
        self.threadpool.clear()
    
    def port_changed(self, s):
        '''
        Trigger when combo arduino box changed
        '''
        self.currentPortName = s
    
    def changePage(self, index):
        '''
        Navigate between main pages
        0 = Tracker Page
        1 = Login Page
        2 = Create Page
        '''
        self.stackedWidgetMain.setCurrentIndex(index)

    def update_plot_graph(self, new_y):
        '''
        Update Graph Data
        '''
        global flagTime, flagHiddenGraph, delayTime
        try:
            # Add time to X (from delayTime to 1 seconds)
            if(flagTime > 1/delayTime):
                flagTime = 0
                self.seconds = np.append(self.seconds, self.seconds[-1]+1)
            else:
                flagTime += 1

            self.x = np.append(self.x, self.x[-1] + delayTime)  
            self.y = np.append(self.y, new_y[9])  
            
            # If button was pressed, change it to red line
            if new_y[10] == 1:
                # Get the max
                if new_y[9] > self.currentMax:
                    self.currentMax = new_y[9]
                
                # Get the min
                if new_y[9] < self.currentMin:
                    self.currentMin = new_y[9]
                
                # Only active when the first change
                if flagHiddenGraph == False:
                    self.currentMin = 0
                    self.currentMax = 0
                    self.currentRate = 0
                    self.total = 0
                    self.hidden = np.array([])
                    self.hidden_x = np.array([])
                flagHiddenGraph = True

                self.total += new_y[9]
                
                length = len(self.hidden) if len(self.hidden) > 0 else 1
                self.currentRate = self.total / length                
                
                # Get the Array of Red Line Graph
                self.hidden = np.append(self.hidden, new_y[9])
                self.hidden_x = np.append(self.hidden_x, self.x[-1])
            else:
                # Set back the flag to False
                if flagHiddenGraph == True:
                    flagHiddenGraph = False

            # If time has exceeds 30 seconds, move the graph
            if(len(self.seconds) > 30):
                self.xRange += delayTime
                self.graphWidget.setXRange(self.xRange, self.xRange+50, padding=0)
                self.miniGraphWidget.setXRange(self.xRange, self.xRange+50, padding=0)
            
            # yRange = self.y[-(30//delayTime):-1] if len(self.y) > 30//delayTime else self.y[:-1]
            # upperRange = np.amax(yRange) + 10
            # lowerRange = np.amin(yRange) - 10 if np.amin(yRange) - 10 < 0 else 0
            # self.graphWidget.setYRange(lowerRange, upperRange, padding=0)
                        
            # Append the sensor value
            self.sensorA = np.append(self.sensorA, new_y[0])
            self.sensorB = np.append(self.sensorB, new_y[1])
            self.sensorC = np.append(self.sensorC, new_y[2])
            self.sensorD = np.append(self.sensorD, new_y[3])
            self.sensorE = np.append(self.sensorE, new_y[4])
            self.sensorF = np.append(self.sensorF, new_y[5])
            self.sensorG = np.append(self.sensorG, new_y[6])
            self.sensorH = np.append(self.sensorH, new_y[7])
            self.sensorI = np.append(self.sensorI, new_y[8])
            
            self.data_line.setData(self.x, self.y)
            self.hidden_line.setData(self.hidden_x, self.hidden, connect="finite")
            self.setCurrentMiniData(self.currentMiniY)
        except:
            self.stopThreading()

    def setCurrentMiniData(self, index):
        '''
        Set current mini data
        '''
        if index == 'A':
            self.mini_data_line.setData(self.x, self.sensorA)
        elif index == 'B':
            self.mini_data_line.setData(self.x, self.sensorB)
        elif index == 'C':
            self.mini_data_line.setData(self.x, self.sensorC)
        elif index == 'D':
            self.mini_data_line.setData(self.x, self.sensorD)    
        elif index == 'E':
            self.mini_data_line.setData(self.x, self.sensorE)
        elif index == 'F':
            self.mini_data_line.setData(self.x, self.sensorF)
        elif index == 'G':
            self.mini_data_line.setData(self.x, self.sensorG)
        elif index == 'H':
            self.mini_data_line.setData(self.x, self.sensorH)
        elif index == 'I':
            self.mini_data_line.setData(self.x, self.sensorI)
        else:
            return
    
    def switchMiniGraph(self, arrow):
        '''
        Switch between mini graph
        '''
        sensorPositions = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        currentIndex = sensorPositions.index(self.currentMiniY)
        if arrow == 'L':
            self.currentMiniY = sensorPositions[currentIndex - 1]
        elif arrow == 'R':
            if currentIndex == len(sensorPositions) - 1:
                self.currentMiniY = sensorPositions[0]
            else:
                self.currentMiniY = sensorPositions[currentIndex + 1]

        self.miniGraphWidget.setTitle('Graph for sensor {}'.format(self.currentMiniY), color="#F59100", size="10pt")
    
    def login(self):
        if (self.loginPatientId ==""):
            messageError('Error Input', 'ID cannot be empty')
            return
        try:
            patient = self.db.child(self.loginPatientId).get()
            self.currentPatient = {   
                    "id": self.loginPatientId,
                    "name": patient.val()["name"],
                    "age": patient.val()["age"],
                    "gender": patient.val()["gender"],
                    "max": patient.val()["max"],
                    "min": patient.val()["min"],
                    "rate": patient.val()["rate"]
            }
            self.label_name.setText(patient.val()["name"])
            self.label_gender.setText( patient.val()["gender"])
            self.label_age.setText(str(patient.val()["age"]) + " Years Old")
            self.label_min.setText("Min : " + str(patient.val()["min"]))
            self.label_rate.setText("Rate : " + str(patient.val()["rate"]))
            self.label_max.setText("Max : " + str(patient.val()["max"]))
            self.changePage(0)
        except:
            messageError('Error Input', 'False ID or Error connecting to Database')
            return


    def save(self):
        if (self.curr_working):
            self.stopThreading()
            Worker.flagThread = True
        try:
            self.region.setRegion([self.currentMin, self.currentMax])
            patient = self.db.child(self.currentPatient['id']).update({"max": self.currentMax, "min": self.currentMin, "rate": self.currentRate})
            self.label_min.setText("Min : " + str(self.currentMin))
            self.label_rate.setText("Rate : " + str(self.currentRate))
            self.label_max.setText("Max : " + str(self.currentMax))
        except:
            messageError('Error', 'Error connecting to database')
            return

    def create(self): 
        if(self.createPatientId == '') or (self.createPatientName == "") or (self.createPatientAge == "") or (self.createPatientGender == ""):
            messageError('Error Input', 'Please fill all the box needed')
            return
        elif not (self.createPatientAge.isnumeric()):
            messageError('Error Input', 'Age must be a number')
            return
        try:
            id_patient = self.createPatientId
            patient = {  
                    "id": self.createPatientId,
                    "name": self.createPatientName,
                    "age": int(self.createPatientAge),
                    "gender": self.createPatientGender,
                    "max": 0,
                    "min": 0,
                    "rate": 0
            }
            self.db.child(id_patient).set(patient)
            self.label_name.setText(self.createPatientName)
            self.label_gender.setText(self.createPatientGender)
            self.label_age.setText(self.createPatientAge + " Years Old")
            self.label_min.setText("Min : 0")
            self.label_rate.setText("Rate : 0")
            self.label_max.setText("Max : 0")
            self.currentPatient = patient
            self.changePage(0)
        except:
            messageError('Error', 'Error connecting to database')
            return

    def databaseButton(self):
        if (self.curr_working):
            self.stopThreading()
            Worker.flagThread = True
        try:
            dataPatient = self.db.get()

            self.patientTable.setRowCount(len(dataPatient.each()))  
            count_row = 0
            for patient in dataPatient.each():
                self.patientTable.setItem(count_row ,0, QTableWidgetItem(patient.key())) 
                self.patientTable.setItem(count_row ,1, QTableWidgetItem(patient.val()["name"])) 
                self.patientTable.setItem(count_row ,2, QTableWidgetItem(str(patient.val()["age"]))) 
                self.patientTable.setItem(count_row ,3, QTableWidgetItem(patient.val()["gender"])) 
                self.patientTable.setItem(count_row ,4, QTableWidgetItem(str(patient.val()["max"]))) 
                self.patientTable.setItem(count_row ,5, QTableWidgetItem(str(patient.val()["min"])))
                self.patientTable.setItem(count_row ,6, QTableWidgetItem(str(patient.val()["rate"])))
                count_row += 1

            self.changePage(1)
            self.stackedWidget.setCurrentWidget(self.page_2)
            self.region.setRegion([0, 0])

        except:
            messageError('Error', 'Error connecting to database')
            return

    def trackerButton(self):
        if (self.curr_working):
            self.stopThreading()
            Worker.flagThread = True
        self.changePage(1)
        self.stackedWidget.setCurrentWidget(self.page_1)
        self.region.setRegion([0, 0])
        
        # Main Graph Value
        self.x = np.array([0])  
        self.y = np.array([0])  
        self.hidden_x = np.array([0])
        self.hidden = np.array([0])
        self.seconds = np.array([0])
        self.xRange = 0

        # Mini Graph Value
        self.sensorA = np.array([0])
        self.sensorB = np.array([0])
        self.sensorC = np.array([0])
        self.sensorD = np.array([0])
        self.sensorE = np.array([0])
        self.sensorF = np.array([0])
        self.sensorG = np.array([0])
        self.sensorH = np.array([0])
        self.sensorI = np.array([0])
        self.currentMiniY = 'A'
        self.data_line.setData(self.x, self.y)
        self.hidden_line.setData(self.hidden_x, self.hidden)
        self.mini_data_line.setData(self.x, self.sensorA)

    def refreshClick(self):
        self.serialPorts = serial_ports()
        self.comboBoxArd.clear()
        self.comboBoxArd.addItems(self.serialPorts)
        
    def create_id(self, s):
        self.createPatientId = s

    def create_name(self, s):
        self.createPatientName = s

    def create_age(self, s):
        self.createPatientAge = s

    def create_gender(self, s):
        self.createPatientGender = s
    
    def login_id(self, s):
        self.loginPatientId = s


if __name__ == "__main__":
    appctxt = ApplicationContext()
    window = MainWindow()
    window.show()
    sys.exit(appctxt.app.exec_())



    