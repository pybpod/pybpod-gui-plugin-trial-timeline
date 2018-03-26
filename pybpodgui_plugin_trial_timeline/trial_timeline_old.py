import logging
import matplotlib.pyplot as plt
import numpy as np

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

logger = logging.getLogger(__name__)

class TrialTimeline_old(BaseWidget):
    """ Plugin main window """

    def __init__(self, session):
        BaseWidget.__init__(self, session.name)

        self.session = session

        self.set_margin(5)

        self._reload      = ControlButton('Reload everything')
        self._graph 		= ControlMatplotlib('Value')

        self.formset = [
			'_reload',
			'_graph'			
		]

        self._graph.on_draw = self.__on_draw_evt
        self._reload.value = self.__reload_evt
    
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
        self.read_data()

    def read_data(self, update_gui = False):
        # timers will be implemented later
        messages = self.session.messages_history

        getting_trial = False
        first_state_message = True

        trialstates = []
        trial_list = []
        filteredstates = []

        for msg in messages:
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
                
                print('final states for this trial')
                for fs in filteredstates:
                    print(fs.tolist())
                
                trial_list.append(filteredstates)
                
                trialstates = []
                filteredstates = []
        
        print('final thing')
        for a in trial_list:
            print(a)
        
        #let's assume the trial list contains same size trials and the states are all the same:
        numtrials = len(trial_list)
        numstates = 0
        graph_x = []
        graph_xl = []
        graph_y = []
        if numtrials > 0:
            numstates = len(trial_list[0])
        print('trials',trial_list)
        print('numtrials',numtrials)
        print('numstates',numstates)
        graphdata = np.zeros((numstates,numtrials))
        print(graphdata)
        for i in range(len(trial_list)):
            graph_x.append(i)
            graph_xl.append('trial '+str(i))
            for j in range(len(trial_list[i])):
                graphdata[j][i] = (float(trial_list[i][j].end_timestamp) + i*0.05) - float(trial_list[i][j].start_timestamp)
        
        print(graphdata)

        coloring = ['red','blue','green','yellow']
        offset = np.zeros(len(graph_x))
        for i in range(len(graphdata)):
            print(graph_x,graphdata[i])
            print(coloring[i])
            plt.barh(graph_x,graphdata[i],height=0.8,color=coloring[i],left=offset)
            offset = offset + graphdata[i]
        plt.yticks(graph_x,graph_xl)
        plt.show()


    def hide(self):
        self._timer.stop()
        self._stop = True

    @property
    def mainwindow(self):
        return self.session.mainwindow

    @property
    def title(self):
        return BaseWidget.title.fget(self)
    
    @title.setter
    def title(self, value):
        BaseWidget.title.fset(self, 'Trial Timeline: {0}'.format(value))
    