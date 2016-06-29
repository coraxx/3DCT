#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Colored stdout status powered by "Colorama".

Usage:
	import clrmsg
then call e.g.:
	print(clrmsg.ERROR + 'Error message')
and it will print:
	[ ERROR ] Error message

# @Title			: clrmsg
# @Project			: 3DCTv2
# @Description		: Colored stdout status powered by "Colorama"
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			: Arnon Yaari
# 					: https://github.com/tartley/colorama
# @Maintainer		: Jan Arnold
# @Date				: 2016/02
# @Version			: 3DCT 2.1.0 module rev. 1
# @Status			: stable
# @Usage			: import clrmsg
# 					: then call e.g. # print(clrmsg.ERROR + 'Error message')
# 					: and it will return # [ ERROR ] Error message
# @Notes			: You can add your own status prefixes.
# @Python_version	: 2.7.11
"""
# ======================================================================================================================

## Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
## Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
## Style: DIM, NORMAL, BRIGHT, RESET_ALL

try:
	import colorama
	clrm_import = True
	colorama.init(autoreset=True)
	## prefixes
	DEBUG = '[ ' + colorama.Fore.BLUE + colorama.Style.BRIGHT + 'DEBUG' + colorama.Style.RESET_ALL + ' ] '
	OK = '[ ' + colorama.Fore.GREEN + colorama.Style.BRIGHT + ' OK  ' + colorama.Style.RESET_ALL + ' ] '
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
	if clrm_import is True:
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
