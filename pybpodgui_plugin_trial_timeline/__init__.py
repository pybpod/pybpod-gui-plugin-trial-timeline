# !/usr/bin/python3
# -*- coding: utf-8 -*-

__version__ = "1.0.0"
__author__ = "Sérgio Copeto"
__credits__ = ["Sérgio Copeto", "Ricardo Ribeiro"]
__license__ = "Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>"
__maintainer__ = ["Sérgio Copeto", "Ricardo Ribeiro"]
__email__ = ["ricardojvr@gmail.com"]
__status__ = "Development"

from confapp import conf

conf += 'pybpodgui_plugin_trial_timeline.settings'
#conf += 'pybpodgui_plugin_trial_timeline.resources'


import loggingbootstrap

# setup different loggers but output to single file
loggingbootstrap.create_double_logger("pybpodgui_plugin_trial_timeline", conf.APP_LOG_HANDLER_CONSOLE_LEVEL,
									  conf.APP_LOG_FILENAME,
									  conf.APP_LOG_HANDLER_FILE_LEVEL)