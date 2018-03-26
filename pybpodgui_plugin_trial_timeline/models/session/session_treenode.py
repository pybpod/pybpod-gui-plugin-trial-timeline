# !/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from pyforms import conf

from AnyQt.QtGui import QIcon
from pyforms.controls import ControlTree

from pybpodgui_plugin_trial_timeline.trial_timeline import TrialTimeline

logger = logging.getLogger(__name__)

class SessionTreeNode(object):

    def create_treenode(self, tree):
        node = super(SessionTreeNode, self).create_treenode(tree)

        self.trialtimeline_action = tree.add_popup_menu_option(
            'Trial Timeline', 
            self.open_trialtimeline_window,
            item=self.node
            )

        self.trialtimeline_action = tree.add_popup_menu_option(
            'Trial Timeline (Detached)', 
            self.open_trialtimeline_window_detached,
            item=self.node
            )

        return node

    def open_trialtimeline_window(self):
        # little helper so we can load the events from the csv
        super(SessionTreeNode, self).node_double_clicked_event()

        print('opening trial timeline')
        if not hasattr(self,'trial_timeline_win'):
            self.trial_timeline_win = TrialTimeline(self)
            self.trial_timeline_win.show()
        else:
            self.trial_timeline_win.show()
    
    def open_trialtimeline_window_detached(self):
        # little helper so we can load the events from the csv
        super(SessionTreeNode, self).node_double_clicked_event()
        
        print('opening trial timeline (DETACHED)')
        if not hasattr(self,'trial_timeline_win'):
            self.trial_timeline_win = TrialTimeline(self)
            self.trial_timeline_win.show(True)
        else:
            self.trial_timeline_win.show(True)
    
    @property
    def name(self):
        return super(SessionTreeNode, self.__class__).name.fget(self)

    @name.setter
    def name(self, value):
        super(SessionTreeNode, self.__class__).name.fset(self, value)
        if hasattr(self, 'trialsplot_win'):
            self.trialsplot_win.title = value 
    

