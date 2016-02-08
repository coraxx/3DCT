#!/usr/bin/env python
#title				: scatterHistPlot.py
#description		: Draw a scatter plot with axis histograms
#author				: Jan Arnold
#email				: jan.arnold (at) coraxx.net
#credits			: http://matplotlib.org/examples/axes_grid/scatter_hist.html
#maintainer			: Jan Arnold
#date				: 2015/10
#version			: 0.1
#status				: developement
#usage				: import scatterHistPlot.py and call main(x,y), where x 
#					  and y are numpy arrays
#notes				: 
#python_version		: 2.7.10 
#=================================================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable

def closeAll():
	plt.close("all")

def main(x='random',y='random',frame=False,framesize=None,xlabel="",ylabel=""):
	# defaults behave funny between windows and mac os x. PyQT4 backend seems to work fine on both
	plt.switch_backend("qt4agg")
	if x == 'random' or y == 'random':
		# the random data
		x = np.random.randn(1000)
		y = np.random.randn(1000)

	fig, axScatter = plt.subplots(figsize=(5.5,5.5))
	print plt.get_backend()
	# the scatter plot:
	axScatter.scatter(x, y)
	axScatter.set_aspect(1.)
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	axScatter.plot([0], '+', mew=1, ms=10, c="red")

	if frame == True and framesize != None:
		axScatter.add_patch(patches.Rectangle( (-framesize*0.5, -framesize*0.5),
							framesize,framesize,fill=False,edgecolor="red"))
	elif frame == True and framesize == None:
		print "Please specify frame size in px as e.g. framesize=1.86"

	# create new axes on the right and on the top of the current axes
	# The first argument of the new_vertical(new_horizontal) method is
	# the height (width) of the axes to be created in inches.
	divider = make_axes_locatable(axScatter)
	axHistx = divider.append_axes("top", 1.2, pad=0.1, sharex=axScatter)
	axHisty = divider.append_axes("right", 1.2, pad=0.1, sharey=axScatter)

	# make some labels invisible
	plt.setp(axHistx.get_xticklabels() + axHisty.get_yticklabels(),
	         visible=False)

	# now determine nice limits by hand:
	binwidth = 0.25
	xymax = np.max( [np.max(np.fabs(x)), np.max(np.fabs(y))] )
	lim = ( int(xymax/binwidth) + 1) * binwidth

	bins = np.arange(-lim, lim + binwidth, binwidth)
	axHistx.hist(x, bins=bins)
	axHisty.hist(y, bins=bins, orientation='horizontal')

	# the xaxis of axHistx and yaxis of axHisty are shared with axScatter,
	# thus there is no need to manually adjust the xlim and ylim of these
	# axis.

	#axHistx.axis["bottom"].major_ticklabels.set_visible(False)
	for tl in axHistx.get_xticklabels():
	    tl.set_visible(False)
	#axHistx.set_yticks([0, 50, 100])

	#axHisty.axis["left"].major_ticklabels.set_visible(False)
	for tl in axHisty.get_yticklabels():
	    tl.set_visible(False)
	#axHisty.set_xticks([0, 50, 100])

	plt.draw()
	plt.show()

if __name__ == '__main__':
	main()