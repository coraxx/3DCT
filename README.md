# README #

This Toolbox is build for 3D correlative microscopy. It helps with 3D to 2D correlation of three dimensional confocal image stacks to two dimensional SEM/FIB dual beam microscope images. Though it is not limited to that.

The 3D Correlation Toolbox was developed at the Max Planck Institute of Biochemistry, Department of Molecular Structural Biology on the basis of the paper [Site-Specific Cryo-focused Ion Beam Sample Preparation Guided by 3D Correlative Microscopy](http://dx.doi.org/10.1016/j.bpj.2015.10.053)

Further information can be found on [http://www.biochem.mpg.de/en/rd/baumeister](http://www.biochem.mpg.de/en/rd/baumeister) and [http://3dct.semper.space](http://3dct.semper.space)

The Toolbox is written in Python 2.7 and comes with a PyQt4 GUI. Further dependencies as of now are:

* PyQt4 [^1]
+ numpy [^2]
+ scipy [^2]
+ matplotlib [^2]
+ opencv [^1]
+ cv2 [^2]
+ tifffile [^2]  (Christoph Gohlke)
+ colorama [^2]  (optional for colored stdout when debugging)

[^1]: usually available via your favorite package manager
[^2]: available via pip

A test dataset can be downloaded here: [http://3dct.semper.space/download/3D_correlation_test_dataset.zip](http://3dct.semper.space/download/3D_correlation_test_dataset.zip)

An introduction video can be viewed here: [https://www.youtube.com/watch?v=nZnUZ877-TU](https://www.youtube.com/watch?v=nZnUZ877-TU)

### License ###

Copyright (C) 2016  Jan Arnold

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.

### Version ###

Version 2.0 is the first public release and received a revised GUI and image stack handling (reslicing) done in python (formerly outsourced to FIJI)

### Binaries ###

There are [Pyinstaller](http://www.pyinstaller.org) binaries available for Mac OS X, Windows, and Linux (built under Ubuntu 15.04) at [http://3dct.semper.space/](http://3dct.semper.space/#download)

### Citing ###

We ask users to cite:

* The general [paper](http://dx.doi.org/10.1016/j.bpj.2015.10.053) that forms the basis of the 3D Correlation Toolbox
+ When using independent modules/scripts from the source code, any [specific](http://3dct.semper.space/documentation.html#citable) publications of modules/scripts used in this software
+ Check the header of the module/script in question for more detailed information

If journal reference limits interfere, the module/script-specific publications should take precedence.

In general, please cite this project and the modules/scripts used in it.

Thank you for your support!

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact