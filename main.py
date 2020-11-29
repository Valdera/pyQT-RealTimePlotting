from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys
import platform
import time
from random import randint
from ui_main import Ui_MainWindow
from ui_functions import *
from worker import Worker
flagTime = 0
flagThread = True
delayTime = 0.2

def initButton(self):
    self.Btn_Toggle.clicked.connect(lambda: UIFunctions.toggleMenu(self, 250, True))
    self.btn_page_1.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_1))
    self.btn_page_2.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_2))
    self.btn_page_3.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_3))
    self.startButton.pressed.connect(lambda: self.execute_thread())
    self.stopButton.pressed.connect(lambda: self.stopThreading())

def initGraph(self):
    self.graphWidget.setBackground('w')
    self.graphWidget.setTitle("Your Title Here", color="b", size="30pt")
    styles = {"color": "#f00", "font-size": "20px"}
    self.graphWidget.setLabel("left", "Temperature (°C)", **styles)
    self.graphWidget.setLabel("bottom", "Hour (H)", **styles)
    pen = pg.mkPen(color='r', width=5)
    self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)
    self.xRange = int(self.y[0])
    self.graphWidget.setXRange(self.xRange, self.xRange+50, padding=0)
    self.graphWidget.showGrid(x=True, y=True)

class MainWindow(QMainWindow,Ui_MainWindow):
    def __init__(self, *args, obj=None,**kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.threadpool = QThreadPool()
       
        initButton(self)

        # Graph init
        graphLayout = QVBoxLayout()
        self.graphWidget = pg.PlotWidget()
        graphLayout.addWidget(self.graphWidget)
        self.frameGraph.setLayout(graphLayout)

        # Graph Value
        self.x = [0]  # 100 time points
        self.y = [0]  # 100 data points
        self.seconds = [0]

        # Graph GUI
        initGraph(self)

    def stopThreading(self):
        Worker.flagThread = False

        # self.graphWidget.clear()
    def execute_this_fn(self):
        global delayTime
        y = randint(0, 10)
        time.sleep(delayTime)
        return y 

    def thread_complete(self):
        Worker.flagThread = True
        print("THREAD COMPLETE")
    
    def result_process(self, new_y):
        self.update_plot_data(new_y)


    def execute_thread(self):
        # Execute
         # Pass the function to execute
        worker = Worker(self.execute_this_fn) 
        worker.signals.result.connect(self.result_process)
        worker.signals.finished.connect(self.thread_complete)
        self.threadpool.start(worker)

    def closeEvent(self, event):
        Worker.flagThread = False
        self.threadpool.clear()

    def update_plot_data(self, new_y):
        global flagTime, delayTime
        if(flagTime > 1/delayTime):
            # self.graphWidget.setYRange(30, 40, padding=0)
            flagTime = 0
            self.seconds.append(self.seconds[-1]+1)
        else:
            flagTime += 1
        
        if(len(self.seconds) > 30):
            self.xRange += delayTime
            print(self.xRange)
            self.graphWidget.setXRange(self.xRange, self.xRange+50, padding=0)

        self.x.append(self.x[-1] + delayTime)  # Add a new value 1 higher than the last.
        # self.y = self.y[1:]  # Remove the first 
        self.y.append(new_y)  # Add a new random value.
        self.data_line.setData(self.x, self.y)  # Update the data.

    def update_plot(self):
        # Drop off the first y element, append a new one.
        self.ydata = self.ydata[1:] + [random.randint(0, 10)]
        self.canvas.axes.cla()  # Clear the canvas.
        self.canvas.axes.plot(self.xdata, self.ydata, 'r')
        # Trigger the canvas to update and redraw.
        self.canvas.draw()


    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
