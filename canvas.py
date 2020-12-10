from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.set_title("Main Graph")
        self.axes.set_xlabel("Seconds")
        self.axes.set_ylabel("Millimeter")
        super(MplCanvas, self).__init__(fig)
    
    def updateRange(self,min_x,max_x):
        self.axes.set_xlim(xmin= min_x, xmax = max_x)
        self.axes.set_ylim(ymin= 0, ymax = 15)

def initCanvas(self):
    self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
    toolbar = NavigationToolbar(self.canvas, self)
    self._plot_ref = None


     # Update Matplotlib Graph
# def update_plot(self, new_y):
#     global flagTime, delayTime
#     if(flagTime > 1/delayTime):
#         flagTime = 0
#         self.seconds.append(self.seconds[-1]+1)
#     else:
#         flagTime += 1
#     self.y.append(new_y)
#     # self.x.append(self.x[-1] + delayTime)
#     self.canvas.axes.cla()  # Clear the canvas.
#     self.canvas.axes.plot(self.x, self.y, 'r')
#     if(len(self.seconds) >= 15):
#         self.x = self.x[1:]
#         self.y = self.y[1:]
#         self.xRange += delayTime
#     self.canvas.updateRange(self.xRange, self.xRange + 20)
#     self.canvas.draw()
