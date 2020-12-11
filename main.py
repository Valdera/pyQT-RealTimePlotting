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
from random import randint
from ui_main import Ui_MainWindow
from ui_functions import *
from worker import Worker
from canvas import MplCanvas
import numpy as np

flagTime = 0
flagThread = True
delayTime = 0.05

# TODO :
# -- CHANGE ARRAY TO NUMPY ARRAY
# -- IMPLEMENT HIDDEN LINE
# -- FIX HEIGHT ADJUST
# -- SET RANGE IN MINI GRAPH
# -- MAKE LOGIN UI
# -- MAKE DATA TRANSFORMATION ARCHITECTURE
# -- CONFIGURE WITH FIREBASE
# -- CRUD OPERATIONS


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
    # self.Btn_Toggle.clicked.connect(lambda: UIFunctions.toggleMenu(self, 250, True))
    self.btn_page_1.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_1))
    self.btn_page_2.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_2))
    self.btn_page_3.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_3))
    self.startButton1.pressed.connect(lambda: self.execute_thread())
    self.stopButton1.pressed.connect(lambda: self.stopThreading())
    self.createButton.pressed.connect(lambda: self.changePage(0))
    self.graphRightButton.pressed.connect(lambda: self.switchMiniGraph('R'))
    self.graphLeftButton.pressed.connect(lambda: self.switchMiniGraph('L'))


def initGraph(self):
    '''
    Init the main graph
    '''
    # Plot the graph
    self.graphWidget = pg.PlotWidget()
    
    # GUI Configuration
    self.graphWidget.setBackground('w')
    self.graphWidget.setTitle("Main Graph", color="#F59100", size="13pt")
    styles = {"color": "#F59100", "font-size": "20px"}
    self.graphWidget.setLabel("left", "Range (mm)", **styles)
    self.graphWidget.setLabel("bottom", "Seconds (s)", **styles)
    pen = pg.mkPen(color='#F59100', width=2)
    
    # Set the data for the graph
    self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)
    # self.hidden_line = self.graphWidget.plot(self.x, self.)
    
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
    stringArr = str(i)[2:].split(";")[:-1]
    if (stringArr[0][:1] == "\\"):
        stringArr[0] = 0
    arr = [int(i) for i in stringArr]
    return arr
 

class MainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self, *args, obj=None,**kwargs):
        '''
        Init class
        '''
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.threadpool = QThreadPool()
        self.stackedWidgetMain.setCurrentIndex(1)
       
        initButton(self)
        # Make the stop button invisible
        self.stopButton1.setHidden(True)

        # Get all serial ports currently connected
        self.serialPorts = serial_ports()
        self.comboBoxArd.addItems(self.serialPorts)
        self.currentPortName = self.serialPorts[0]
        self.comboBoxArd.currentIndexChanged[str].connect(self.port_changed);

        # Main Graph Value
        self.x = [0]  
        self.y = [0]  
        self.seconds = [0]
        self.xRange = 0

        # Mini Graph Value
        self.sensorA = [0]
        self.sensorB = [0]
        self.sensorC = [0]
        self.sensorD = [0]
        self.sensorE = [0]
        self.sensorF = [0]
        self.sensorG = [0]
        self.sensorH = [0]
        self.sensorI = [0]

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
        global delayTime
        y = randint(0, 10)
        line = self.currentPort.readline()
        filtered = filterInput(line)
        time.sleep(delayTime)
        print(filtered)

        return filtered
            

    def thread_complete(self):
        '''
        This function run after thread finished
        '''
        self.startButton1.setHidden(False)
        self.stopButton1.setHidden(True)
        Worker.flagThread = True
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
        self.startButton1.setHidden(True)
        self.stopButton1.setHidden(False)
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
        self.currentPortName = s; 
        print(self.currentPortName)
    
    def changePage(self, index):
        self.stackedWidgetMain.setCurrentIndex(index)

    def update_plot_graph(self, new_y):
        '''
        Update Graph Data
        '''
        global flagTime, delayTime
        try:
            if(flagTime > 1/delayTime):
                flagTime = 0
                self.seconds.append(self.seconds[-1]+1)
            else:
                flagTime += 1
            
            if(len(self.seconds) > 30):
                self.xRange += delayTime
                print(self.xRange)
                # self.graphWidget.setYRange(30, 40, padding=0)
                self.graphWidget.setXRange(self.xRange, self.xRange+50, padding=0)

            self.x.append(self.x[-1] + delayTime)  # Add a new value 1 higher than the last.
            self.y.append(new_y[9])  # Add a new random value.
            
            self.sensorA.append(new_y[0])
            self.sensorB.append(new_y[1])
            self.sensorC.append(new_y[2])
            self.sensorD.append(new_y[3])
            self.sensorE.append(new_y[4])
            self.sensorF.append(new_y[5])
            self.sensorG.append(new_y[6])
            self.sensorH.append(new_y[7])
            self.sensorI.append(new_y[8]+10)

            self.data_line.setData(self.x, self.y)
            self.data_line.setData(self.x, self.sensorI)
            self.setCurrentMiniData(self.currentMiniY)
        
        except:
            self.stopThreading()

    def setCurrentMiniData(self, index):
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())



    