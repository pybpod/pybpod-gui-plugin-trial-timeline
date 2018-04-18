import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random

from pyforms import conf

from pyforms import BaseWidget
from pyforms.controls import ControlProgress
from pyforms.controls import ControlButton
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlList
from pyforms.controls import ControlBoundingSlider
from pyforms.controls import ControlMatplotlib
from AnyQt.QtWidgets import QApplication
from AnyQt.QtGui import QColor, QBrush
from AnyQt.QtCore import QTimer, QEventLoop, QAbstractTableModel, Qt, QSize, QVariant, pyqtSignal

#######################################################################
##### MESSAGES TYPES ##################################################
#######################################################################
from pybpodapi.com.messaging.error   import ErrorMessage
from pybpodapi.com.messaging.debug   import DebugMessage
from pybpodapi.com.messaging.stderr  import StderrMessage
from pybpodapi.com.messaging.stdout  import StdoutMessage
from pybpodapi.com.messaging.warning import WarningMessage
from pybpodapi.com.messaging.parser  import MessageParser

from pybpodapi.com.messaging.trial                  import Trial
from pybpodapi.com.messaging.end_trial              import EndTrial
from pybpodapi.com.messaging.event_occurrence       import EventOccurrence
from pybpodapi.com.messaging.state_occurrence       import StateOccurrence
from pybpodapi.com.messaging.softcode_occurrence    import SoftcodeOccurrence
from pybpodapi.com.messaging.event_resume           import EventResume
from pybpodapi.com.messaging.session_info           import SessionInfo
#######################################################################
#######################################################################

from pybpodgui_api.models.session import Session

class TrialTimeline(BaseWidget):

    def __init__(self, session : Session):
        BaseWidget.__init__(self, session.name)

        self.session = session

        self.set_margin(5)

        self._reload      = ControlButton('Reload everything')
        self._graph 		= ControlMatplotlib('Value')

        self.coloring = ['red','blue','green','yellow']
        self.messages = []
        self._timer = QTimer()
        self._timer.timeout.connect(self.update)
        
        self._read = 0
        self.i = 0

        self.formset = [
			'_graph'			
		]

        self.msgtype = 0
        self.pctime = 1
        self.initialtime = 2
        self.finaltime = 3
        self.messagecontent = 4
        self.info = 5

        self._graph.on_draw = self.__on_draw_evt
        self._reload.value = self.__reload_evt

    def __on_draw_evt(self, figure):
        axes = figure.add_subplot(111)
        axes.clear()
        offset = np.zeros(len(self.graph_x))
        for i in range(len(self.graphdata)):
            axes.barh(self.graph_x,self.graphdata[i],height=0.8,color=self.coloring[i],left=offset, label = self.graph_y[i])
            offset = offset + self.graphdata[i]
        #axes.yticks(self.graph_x,self.graph_xl)
        axes.set_ylabel('Trials')
        axes.set_xlabel('Time (sec)')
        axes.legend(loc="upper right")
        self._graph.repaint()

    
    def __reload_evt(self):
        return
        #self.update()
        if self._timer.isActive():
            self._timer.stop()
        else:
            self._timer.start(conf.TRIALTIMELINE_PLUGIN_REFRESH_RATE)

    
    def show(self, detached = False):
        if self.session.is_running and self.session.setup.detached:
            return
        
        # Prevent the call to be recursive because of the mdi_area
        if not detached:
            if hasattr(self, '_show_called'):
                BaseWidget.show(self)
                return
            self._show_called = True
            self.mainwindow.mdi_area += self
            del self._show_called
        else:
            BaseWidget.show(self)
        
        self._stop = False # flag used to close the gui in the middle of a loading
        if not self._stop and self.session.is_running:
            self._timer.start(conf.TRIALTIMELINE_PLUGIN_REFRESH_RATE)

        self.update()

    def hide(self):
        self._timer.stop()
        self._stop = True

    def to_struct(self,datarow):
        return

    def read_data(self):
        getting_trial = False

        self.trial_list = []
        trialstates     = []
        filteredstates  = []

        for msg in self.session.data.values:
            if msg[self.msgtype] == Trial.MESSAGE_TYPE_ALIAS:
                getting_trial = False
                filteredstates = []
            elif msg[self.msgtype] == StateOccurrence.MESSAGE_TYPE_ALIAS:
                getting_trial = True                    
                temp = StateOccurrence(msg[self.msgtype],msg[self.initialtime],msg[self.finaltime])
                temp.content = msg[self.messagecontent]
                trialstates.append(temp)
            elif msg[self.msgtype] == EndTrial.MESSAGE_TYPE_ALIAS:
                getting_trial = False
                filteredstates = []
            else:
                getting_trial = False
                filteredstates = []
            
            if getting_trial == False and len(trialstates) > 0:
                for i in range(len(trialstates)):
                    if i == 0:
                        filteredstates.append(trialstates[i])
                    else:
                        if trialstates[i].content == filteredstates[len(filteredstates) - 1].content:
                            filteredstates[len(filteredstates) - 1].end_timestamp = trialstates[i].end_timestamp
                        else:
                            filteredstates.append(trialstates[i])
                
                self.trial_list.append(filteredstates)
                
                trialstates = []
                filteredstates = []

            self._read += 1
        
        if len(trialstates) > 0:
            for i in range(len(trialstates)):
                if i == 0:
                    filteredstates.append(trialstates[i])
                else:
                    if trialstates[i].content == filteredstates[len(filteredstates) - 1].content:
                        filteredstates[len(filteredstates) - 1].end_timestamp = trialstates[i].end_timestamp
                    else:
                        filteredstates.append(trialstates[i])
            
            self.trial_list.append(filteredstates)
            
            trialstates = []
            filteredstates = []

        
        

    def data_to_graph(self):
        self.numtrials = len(self.trial_list)
        self.numstates = 0
        self.graph_x = []
        self.graph_xl = []
        self.graph_y = []
        if self.numtrials > 0:
            self.numstates = len(self.trial_list[0])
        
        self.graphdata = np.zeros((self.numstates,self.numtrials))
        for i in range(len(self.trial_list)):
            self.graph_x.append(i)
            self.graph_xl.append('trial '+str(i))
            for j in range(len(self.trial_list[i])):
                if i == 0:
                    self.graph_y.append(self.trial_list[i][j].content)
                self.graphdata[j][i] = (float(self.trial_list[i][j].end_timestamp)) - float(self.trial_list[i][j].start_timestamp)
                #  + random.uniform(0,0.5)

    '''Takes care of all the session data and transforms it in a graph to be shown in the GUI'''
    def update(self):
        if not self.session.is_running:
            self._timer.stop()
            print('stoped counter')
        print('updating',self.i)
        self.read_data()
        self.data_to_graph()
        self._graph.draw()
        self.i = self.i + 1
    
    @property
    def mainwindow(self):
        return self.session.mainwindow

    
    @property
    def title(self):
        return BaseWidget.title.fget(self)
    
    
    @title.setter
    def title(self, value):
        BaseWidget.title.fset(self, 'Trial Timeline: {0}'.format(value))

    