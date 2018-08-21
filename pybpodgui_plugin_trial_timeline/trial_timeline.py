import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
import traceback

from confapp import conf

from pyforms.basewidget import BaseWidget
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
from pybpodapi.session import Session as APISession
from pybpodgui_api.models.session import Session

from matplotlib import colors as mcolors

class TrialTimeline(BaseWidget):

    COL_MSGTYPE   = 0
    COL_PCTIME    = 1
    COL_INITTIME  = 2
    COL_FINALTIME = 3
    COL_MSG       = 4
    COL_INFO      = 5

    def __init__(self, session : Session):
        BaseWidget.__init__(self, session.name)
        self.set_margin(5)

        self.session = session

        self._reload = ControlButton('Reload')
        self._graph  = ControlMatplotlib('Value')

        self._timer = QTimer()
        self._timer.timeout.connect(self.update)
        
        self._read = 0
        self._deltas = None

        self._last_trial_end = None
        
        self._states_dict = {}
        self._trials_list = []
        
        self.formset = [
            '_graph'            
        ]
        self.colors = list(mcolors.CSS4_COLORS.values())
        
        self._graph.on_draw = self.__on_draw_evt
        self._reload.value = self.__reload_evt

    
    
    def __reload_evt(self):
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

    def read_data(self):
        
        res = self.session.data.query("TYPE in ['END-TRIAL', 'STATE'] or (TYPE == 'INFO' and MSG in ['SESSION-ENDED','TRIAL-BPOD-TIME'])")

        for index, msg in res.iterrows():
            if index<=self._read: continue
            
            if msg[self.COL_MSGTYPE] == EndTrial.MESSAGE_TYPE_ALIAS:
                
                if self._deltas is not None:
                    self._trials_list.append(self._deltas)
                self._deltas = {}
                
            elif msg[self.COL_MSGTYPE] == StateOccurrence.MESSAGE_TYPE_ALIAS:

                state = msg[self.COL_MSG]
                delta = float(msg[self.COL_FINALTIME]) - float(msg[self.COL_INITTIME])

                if state not in self._deltas:
                    # count, delta sum, min delta, max delta
                    self._deltas[state] = [delta]
                    self._states_dict[state] = True
                else:
                    self._deltas[state].append(delta)

            elif msg[self.COL_MSGTYPE] == SessionInfo.MESSAGE_TYPE_ALIAS and \
                 msg[self.COL_MSG]     == APISession.INFO_SESSION_ENDED:

                if self._deltas is not None:
                    self._trials_list.append(self._deltas)

            elif msg[self.COL_MSGTYPE] == SessionInfo.MESSAGE_TYPE_ALIAS and \
                 msg[self.COL_MSG] == APISession.INFO_TRIAL_BPODTIME:
                
                trial_start = msg[self.COL_INITTIME]
                trial_end   = msg[self.COL_FINALTIME]

                if self._last_trial_end is not None:
                    delta                             = float(trial_start)-float(self._last_trial_end)
                    self._deltas['Init lagging']      = [delta]
                    self._states_dict['Init lagging'] = True

                self._last_trial_end = trial_end            


            self._read = index
        

        


    def __on_draw_evt(self, figure):

        try:
            axes = figure.add_subplot(111)
            axes.clear()

            trials_labels  = []
            states_labels  = list(self._states_dict.keys())

            num_states = len(self._states_dict)
            num_trials = len(self._trials_list)
            data       = np.zeros( (num_states, num_trials) )
            errors     = np.zeros( (num_states, num_trials) )
            
            for i, states in enumerate(self._trials_list):
                trials_labels.append( 'Trial {0}'.format(i) )

                for j, state_label in enumerate(states_labels):

                    state_data = states.get(state_label, None)

                    if state_data is not None:
                        data[j][i]   = np.mean(state_data)
                        errors[j][i] = np.std(state_data)

            colors         = {}
            offset         = np.zeros( len(trials_labels) )
            trials_indexes = np.array(range(len(trials_labels)))

            for i, states_data in enumerate(data):
                if len(states_data)==0: continue

                state_label = states_labels[i]
                if state_label not in colors:
                    colors[state_label] = self.colors[len(colors)]

                axes.barh(
                    trials_indexes,
                    states_data,
                    height = 0.8,
                    color  = colors[state_label],
                    left   = offset,
                    label  = state_label,
                    yerr   = errors[i]
                )
                offset = offset + states_data
            
            axes.set_yticks(trials_indexes)
            axes.set_yticklabels(trials_labels)
            axes.set_ylabel('Trials')
            axes.set_xlabel('Time (sec)')
            axes.legend(loc="upper right")
            self._graph.repaint()
        except:
            self.critical( traceback.format_exc(), 'An error occurred')

                
    '''Takes care of all the session data and transforms it in a graph to be shown in the GUI'''
    def update(self):
        if not self.session.is_running:
            self._timer.stop()
        self.read_data()
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

    