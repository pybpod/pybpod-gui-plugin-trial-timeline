from setuptools import setup, find_packages
import re

version = ''
with open('pybpodgui_plugin_trial_timeline/__init__.py', 'r') as fd:
	version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
	                    fd.read(), re.MULTILINE).group(1)

if not version:
	raise RuntimeError('Cannot find version information')

setup(
	name='pybpod-gui-plugin-trial-timeline',
	version=version,
	description="""PyBpod GUI Trial Timeline Plugin""",
	author='Sérgio Copeto',
	author_email='sergio.copeto@research.fchampalimaud.org',
	license='Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>',
	url='https://bitbucket.org/fchampalimaud/pybpod-gui-plugin-trial-timeline/',

	include_package_data=True,
	packages=find_packages(exclude=['contrib', 'docs', 'tests', 'examples', 'deploy', 'reports']),

	package_data={'pybpodgui_plugin_trial_timeline': [
		'resources/*.*',
	]
	},
)