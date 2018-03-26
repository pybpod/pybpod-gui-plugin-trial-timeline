import logging
import matplotlib.pyplot as plt
import numpy as np
import random

from pyforms import conf

from pyforms import conf

from pyforms import BaseWidget
from pyforms.controls import ControlProgress
from pyforms.controls import ControlButton
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlList
from pyforms.controls import ControlBoundingSlider
from pyforms.controls import ControlMatplotlib
from AnyQt.QtWidgets import QApplication
from AnyQt.QtCore    import QTimer

#######################################################################
##### MESSAGES TYPES ##################################################
#######################################################################
from pybranch.com.messaging.error   import ErrorMessage
from pybranch.com.messaging.debug   import DebugMessage
from pybranch.com.messaging.stderr  import StderrMessage
from pybranch.com.messaging.stdout  import StdoutMessage
from pybranch.com.messaging.warning import WarningMessage
from pybranch.com.messaging.parser  import MessageParser

from pybpodapi.com.messaging.trial                  import Trial
from pybpodapi.com.messaging.end_trial              import EndTrial
from pybpodapi.com.messaging.event_occurrence       import EventOccurrence
from pybpodapi.com.messaging.state_occurrence       import StateOccurrence
from pybpodapi.com.messaging.softcode_occurrence    import SoftcodeOccurrence
from pybpodapi.com.messaging.event_resume           import EventResume
from pybpodapi.com.messaging.session_info           import SessionInfo
#######################################################################
#######################################################################

class TrialTimeline(BaseWidget):

    def __init__(self, session):
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

        self.formset = [
			'_reload',
			'_graph'			
		]

        self._graph.on_draw = self.__on_draw_evt
        self._reload.value = self.__reload_evt

    def __on_draw_evt(self, figure):
        axes = figure.add_subplot(111)
        axes.clear()
        offset = np.zeros(len(self.graph_x))
        for i in range(len(self.graphdata)):
            print(self.graph_x,self.graphdata[i])
            print(self.coloring[i])
            axes.barh(self.graph_x,self.graphdata[i],height=0.8,color=self.coloring[i],left=offset, label = self.graph_y[i])
            offset = offset + self.graphdata[i]
        #axes.yticks(self.graph_x,self.graph_xl)
        axes.set_ylabel('Trials')
        axes.set_xlabel('Time (sec)')
        axes.legend(loc="upper right")
        self._graph.repaint()

    
    def __reload_evt(self):
        #self.update()
        if self._timer.isActive():
            self._timer.stop()
        else:
            self._timer.start(100)

    
    def show(self, detached = False):
        if self.session.is_running and self.session.setup.detached:
            return
        
        # Prevent the call to be recursive because of the mdi_area
        if not detached:
            print('calling trial timeline')
            if hasattr(self, '_show_called'):
                BaseWidget.show(self)
                return
            self._show_called = True
            self.mainwindow.mdi_area += self
            del self._show_called
        else:
            print('calling trial timeline (DETACHED)')
            BaseWidget.show(self)
        self.update()

    def read_data(self):
        for i in range(1):
            if self._read < len(self.session.messages_history):
                self.messages.append(self.session.messages_history[self._read])
                self._read = self._read + 1

        ''' Loop throug all the messages and structure them so we can know 
            the number of trials and states per trial'''
        
        # Control variables to know how to group incoming data
        getting_trial = False

        trialstates = []
        self.trial_list = []
        filteredstates = []

        for msg in self.messages:
            if msg.MESSAGE_TYPE_ALIAS == Trial.MESSAGE_TYPE_ALIAS:
                print('TRIAL')
                getting_trial = False
                filteredstates = []
            elif msg.MESSAGE_TYPE_ALIAS == StateOccurrence.MESSAGE_TYPE_ALIAS:
                if not getting_trial:
                    getting_trial = True                    
                trialstates.append(msg)
            elif msg.MESSAGE_TYPE_ALIAS == EndTrial.MESSAGE_TYPE_ALIAS:
                print('END TRIAL')
                getting_trial = False
                filteredstates = []
            else:
                getting_trial = False
                filteredstates = []
            
            if getting_trial == False and len(trialstates) > 0:
                print('compiling trial')
                for i in range(len(trialstates)):
                    print(trialstates[i])
                    if i == 0:
                        filteredstates.append(trialstates[i])
                    else:
                        #print('plim')
                        #print(filteredstates[len(filteredstates)-1][4])
                        if trialstates[i].content == filteredstates[len(filteredstates) - 1].content:
                            #print('equal',trialstates[i].tolist()[4],filteredstates[len(filteredstates) - 1][4])
                            filteredstates[len(filteredstates) - 1].end_timestamp = trialstates[i].end_timestamp
                        else:
                            filteredstates.append(trialstates[i])
                
                self.trial_list.append(filteredstates)
                
                trialstates = []
                filteredstates = []
        
        if len(trialstates) > 0:
            print('compiling trial')
            for i in range(len(trialstates)):
                print(trialstates[i])
                if i == 0:
                    filteredstates.append(trialstates[i])
                else:
                    #print('plim')
                    #print(filteredstates[len(filteredstates)-1][4])
                    if trialstates[i].content == filteredstates[len(filteredstates) - 1].content:
                        #print('equal',trialstates[i].tolist()[4],filteredstates[len(filteredstates) - 1][4])
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
        #print('trials',trial_list)
        #print('numtrials',numtrials)
        #print('numstates',numstates)
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
        self.read_data()
        self.data_to_graph()
        self._graph.draw()
    
    @property
    def mainwindow(self):
        return self.session.mainwindow

    
    @property
    def title(self):
        return BaseWidget.title.fget(self)
    
    
    @title.setter
    def title(self, value):
        BaseWidget.title.fset(self, 'Trial Timeline: {0}'.format(value))

    