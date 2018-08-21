# !/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from confapp import conf

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

        self.trialtimeline_detached_action = tree.add_popup_menu_option(
            'Trial Timeline (Detached)', 
            self.open_trialtimeline_window_detached,
            item=self.node
            )

        return node

    def open_trialtimeline_window(self):
        
        self.load_contents()

        #does not show the window if the detached window is visible
        if hasattr(self, 'trial_timeline_win_detached') and self.trial_timeline_win_detached.visible: return 

        if not hasattr(self,'trial_timeline_win'):
            self.trial_timeline_win = TrialTimeline(self)
            self.trial_timeline_win.show()
        else:
            self.trial_timeline_win.show()
    
    def open_trialtimeline_window_detached(self):
        
        self.load_contents()

        if hasattr(self, 'trial_timeline_win') and self.trial_timeline_win.visible: return 
     
        if not hasattr(self,'trial_timeline_win_detached'):
            self.trial_timeline_win_detached = TrialTimeline(self)
            self.trial_timeline_win_detached.show(True)
        else:
            self.trial_timeline_win_detached.show(True)
    
    @property
    def name(self):
        return super(SessionTreeNode, self.__class__).name.fget(self)

    @name.setter
    def name(self, value):
        super(SessionTreeNode, self.__class__).name.fset(self, value)
        if hasattr(self, 'trialsplot_win'):
            self.trialsplot_win.title = value 
    

