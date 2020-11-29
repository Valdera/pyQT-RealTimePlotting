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
    