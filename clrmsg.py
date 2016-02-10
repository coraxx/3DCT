#!/usr/bin/env python
#title				: clrmsg.py
#description		: Colored stdout status powered by "Colorama"
#author				: Jan Arnold
#email				: jan.arnold (at) coraxx.net
#credits			: Arnon Yaari
#					: https://github.com/tartley/colorama
#maintainer			: Jan Arnold
#date				: 2016/02
#version			: 0.1
#status				: Final
#usage				: import clrmsg
#					: then call e.g. # print(print clrmsg.ERROR + 'Error message')
#					: and it will return # [ ERROR ] Error message
#notes				: You can add your own status prefixes.
#python_version		: 2.7.10 
#=================================================================================

## Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
## Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
## Style: DIM, NORMAL, BRIGHT, RESET_ALL

try:
	import colorama
	clrm_import = True
	colorama.init(autoreset=True)
	## prefixes
	DEBUG = '[ ' + colorama.Fore.BLUE + colorama.Style.BRIGHT + 'DEBUG' + colorama.Style.RESET_ALL + ' ] '
	OK = '[ ' + colorama.Fore.GREEN + colorama.Style.BRIGHT + 'OK   ' + colorama.Style.RESET_ALL + ' ] '
	ERROR = '[ ' + colorama.Fore.RED + colorama.Style.BRIGHT + 'ERROR' + colorama.Style.RESET_ALL + ' ] '
	INFO = '[ ' + colorama.Fore.CYAN + colorama.Style.BRIGHT + 'INFO ' + colorama.Style.RESET_ALL + ' ] '
	WARNING = '[ ' + colorama.Fore.YELLOW + colorama.Style.BRIGHT + 'WARN ' + colorama.Style.RESET_ALL + ' ] '
except:
	print "[ WARNING ] Unable to import colorama. I will pass non colored staus. Use 'pip install colorama' to install the module"
	clrm_import = False

	## prefixes without color if module 'colorama' is not installed
	DEBUG = '[ DEBUG ] '
	OK = '[ OK    ] '
	ERROR = '[ ERROR ] '
	INFO = '[ INFO  ] '
	WARNING = '[ WARN  ] '



def msg(style,msg):
	if clrm_import == True:
		# Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
		# Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
		# Style: DIM, NORMAL, BRIGHT, RESET_ALL
		if style == 'BLUE':
			return '[ ' + colorama.Fore.BLUE + colorama.Style.BRIGHT + 'DEBUG'
		elif style == 'GREEN':
			return '[ ' + colorama.Fore.GREEN + colorama.Style.BRIGHT + 'OK   '
		elif style == 'RED':
			return '[ ' + colorama.Fore.RED + colorama.Style.BRIGHT + 'ERROR'
		elif style == 'CYAN':
			return '[ ' + colorama.Fore.CYAN + colorama.Style.BRIGHT + 'INFO '
		elif style == 'YELLOW':
			return '[ ' + colorama.Fore.YELLOW + colorama.Style.BRIGHT + 'WARN '
	else:
		return msg