from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import traceback, sys


class WorkerSignals(QObject):
  finished = pyqtSignal() # Finished
  error = pyqtSignal(tuple) # Error 
  result = pyqtSignal(object) # Running

class Worker(QRunnable):
    flagThread = True
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
    @pyqtSlot()
    def run(self):
        try:
            while(self.flagThread):
                result = self.fn(*self.args, **self.kwargs)
                self.signals.result.emit(result) # Return the result of the processing

        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit() # Done