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
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar

flagTime = 0
flagThread = True
delayTime = 0.05


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
    self.Btn_Toggle.clicked.connect(lambda: UIFunctions.toggleMenu(self, 250, True))
    self.btn_page_1.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_1))
    self.btn_page_2.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_2))
    self.btn_page_3.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_3))
    self.startButton1.pressed.connect(lambda: self.execute_thread())
    self.stopButton1.pressed.connect(lambda: self.stopThreading())

def initGraph(self):
    '''
    Init the main graph
    '''
    # Plot the graph
    self.graphWidget = pg.PlotWidget()
    # GUI Configuration
    self.graphWidget.setBackground('w')
    self.graphWidget.setTitle("Your Title Here", color="b", size="30pt")
    styles = {"color": "#f00", "font-size": "20px"}
    self.graphWidget.setLabel("left", "Temperature (°C)", **styles)
    self.graphWidget.setLabel("bottom", "Hour (H)", **styles)
    pen = pg.mkPen(color='r', width=2)
    # Set the data and the range
    self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)
    self.graphWidget.setXRange(self.xRange, self.xRange+50, padding=0)
    self.graphWidget.showGrid(x=True, y=True)

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
       
        initButton(self)

        # Get all serial ports currently connected
        self.serialPorts = serial_ports()
        self.comboBoxArd.addItems(self.serialPorts)
        self.currentPortName = self.serialPorts[0]
        self.comboBoxArd.currentIndexChanged[str].connect(self.port_changed);

        # Graph Value
        self.x = [0]  # 100 time points
        self.y = [0]  # 100 data points
        self.seconds = [0]
        self.xRange = 0

        # Graph init
        graphLayout = QVBoxLayout()
        initGraph(self)
        # graphLayout.addWidget(self.canvas)
        # graphLayout.addWidget(toolbar)
        graphLayout.addWidget(self.graphWidget)

        # Insert Layout
        self.frameGraphMain.setLayout(graphLayout)
        self.stopButton1.setHidden(True)

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

        return filtered[0]
            

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

    def update_plot_graph(self, new_y):
        '''
        Update Graph Data
        '''
        global flagTime, delayTime
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
        self.y.append(new_y)  # Add a new random value.
        self.data_line.setData(self.x, self.y)  # Update the data.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())



    