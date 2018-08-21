# !/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from confapp import conf

from AnyQt.QtGui import QIcon
from pyforms.controls import ControlTree

from pybpodgui_plugin_trial_timeline.trial_timeline import TrialTimeline

logger = logging.getLogger(__name__)

class SubjectTreeNode(object):

    def create_sessiontreenode(self, session):
        node = super(SubjectTreeNode, self).create_sessiontreenode(session)

        self.trialtimeline_action = self.tree.add_popup_menu_option(
            'Trial Timeline', 
            session.open_trialtimeline_window,
            item=node
            )

        self.trialtimeline_detached_action = self.tree.add_popup_menu_option(
            'Trial Timeline (Detached)', 
            session.open_trialtimeline_window_detached,
            item=node
            )

        return node