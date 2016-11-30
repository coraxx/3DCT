# Changelog #

## 2.2.2 ##
2016-11-29[^1]

##### Major Changes: #####
- added pytest and unittest tests
- added z height bead extraction "layer option" to context menu
- implemented layer load buttons
- per layer brightness/contrast adjustment selectable over radiobuttons
- show/hide layers
- coloring of rgb images
- option for custom rgb color alongside standard red, green and blue
- option to save the blended images (under options)
- interface changes: custom rotation center was moved to options tab and layer settings are in the control tab
- added single slice view for volumes

##### Minor Changes: #####
- mac path drag and drop update
- added anaconda environment.yml files for linux, mac and windows
- performance improvement for scrolling through stack with coloring enabled
- correlation overlay is now a separate layer
- fine tuned brightness/contrast settings to be consistent when loading different slices and/or saving correlated images with the correct brightness/contrast

##### Bugfixes: #####
- bugfix causing an error in writing the report when the 2D image is missing pixel size information (the function messing it up here will be deprecated soon, so this is just a temporary bugfix)
- bugfix for loading new 3D stacks which were not updating anymore (brightness, contrast, slice...)
- bugfix for leading slash in path in mac os x. Introduced during a Python packages update. Formerly only a problem on linux
- bugfix sorting issue of os.listdir was stacking images incorrectly and showing unsorted file lists
- bugfix linux (kde): filedialog side selection issue in import and export of coordinate files
- bugfix in GUI
- bugfix correct loading of new images (deleting previous "adjusted images")
- bugfix blending handling of none colored images with RGB overlay after correlation
- bugfix in normalizing tool
- bugfix for loading layer (check for same image size/type)
- bugfix for correct coloring on correlated image, both for displaying and saving
- bugfix marker in some situations was stacked behind the image
- bugfix contextmenus deactivated for spinboxes, since that caused problems with control guiding (enable/disable of control elements for better user experience)
- bugfix zero based bug fix for z height
- bugfix for ui element focus when switching back to MIP view while having focus on the slice selector spinbox
- bugfix where checkbox selection broke the MIP<->slice view on windows and linux
- bugfix for some control enable/disable elements when switching between widgets
- fixed some hick-ups with correct brightness/contrast application
- bugfix brightness contrast is applied to every slice that is viewed (was resetting all the time)

## 2.1.0 ##
2016-06-30[^1]

##### Major Changes: #####
- added slice from stack view. Instead of a maximum intensity projection, single slices of 3D image stack volumes can be displayed

##### Minor Changes: #####
- fine tuned brightness/contrast settings to be consistent when loading different slices and/or saving correlated images with the correct brightness/contrast
- the adjusted brightness/contrast is applied to the correlated image which is also displayed in the application. Any further brightness/contrasts adjustments are based on the new image. Hit the "reset image button" if you want to load the original image again.

##### Bugfixes: #####
- fixed some control enable/disable bugs when switching between widgets
- fixed some hick-ups with correct brightness/contrast application

##### Known bugs:#####
- file list order from working directory in 3DCT main window not sorted correctly under Linux (tested under Ubuntu 15.04)
- when changing contrast/brightness and the focus is switched quickly during the process (like clicking on the other image) the order of added markers is not correct anymore. A workaround is to click on the affected image and change the contrast/brightness again, or reset it.


## 2.0.3 ##
2016-06-09[^1]

##### Minor Changes: #####
- added some in-code documentation
- added missing matlab function in matlab rotation script generator
- stack processing of CorrSight sequences now include tiles. They are added in sequence, i.e. stack after stack in one file

##### Bugfixes: #####
- fixed loading of RGB images. Some were imported incorrectly and showed tiling
- coordinate offset calculation for rotation center other than 0,0,0
- matlab rotation script generator variable typo fixed

##### Known bugs:#####
- file list order from working directory in 3DCT main window not sorted correctly under Linux (tested under Ubuntu 15.04)
- when changing contrast/brightness and the focus is switched quickly during the process (like clicking on the other image) the order of added markers is not correct anymore. A workaround is to click on the affected image and change the contrast/brightness again, or reset it.


## 2.0.2 ##
2016-04-27[^1]

##### Minor Changes: #####
- removed broken deprecated poly spline method for extracting z coordinates from beads
- quick help documentation update
- added menu help link to online user's guide

##### Bugfixes: #####
- not disappearing arrows from the residual indication are now removed when resetting the image (correlation module)

##### Known bugs:#####
- file list order from working directory in 3DCT main window not sorted correctly under Linux (tested under Ubuntu 15.04)
- when changing contrast/brightness and the focus is switched quickly during the process (like clicking on the other image) the order of added markers is not correct anymore. A workaround is to click on the affected image and change the contrast/brightness again, or reset it.


## 2.0.1 ##
2016-04-20[^1]

##### Major Changes: #####
- added 2D to 2D and 3D to 3D correlation capabilities. The written report is still tailored towards 2D to 3D correlation though

##### Minor Changes: #####
- small code cosmetics
- errors from correlation were only raised (visible in debug mode in the console). Added message box dialogs for GUI non-console mode
- added reset buttons for image display, i.e. if a correlation was done the reset will clean up the painted correlated marker

##### Bugfixes: #####
- fixed opacity bug in correlation result image



## 2.0.0 ##
2016-04-19[^1]

##### Minor Changes: #####
- added distances of POIs in FIB image from its center (in px and um) for setting the POIs on the SEM/FIB microscope



## 2.0.0 rc1 ##
2016-04-18[^1]

##### Minor Changes: #####
- added marker size and alpha adjustment in correlation module
- global debug switch in tdct/TDCT_debug.py



## 2.0.0 beta 5 ##
2016-04-15[^1]

##### Minor Changes: #####
- focus step size extraction from exif data



## 2.0.0 beta 4 ##
2016-04-07[^1]

##### Bugfixes: #####
- fixed double close() call of correlation widget in case of external call
- fixed RGB tiff imread


## 2.0.0 beta 3 ##
2016-04-05[^1]

##### Major Changes: #####
- function integration complete (finished "normalize" and "Maximum Intensity Projection")

##### Minor Changes: #####
- more precise dialog descriptions
- minor code changes in stack processing (debug handling and process bar)



## 2.0.0 beta 2 ##
2016-03-29[^1]

##### Major Changes: #####
- path handling and validity check for all path selections done

##### Minor Changes: #####
- added quick help buttons

##### Bugfixes: #####
- drop file/dir path on QLineEdit mac bug fixed (http://stackoverflow.com/questions/34689562/pyqt-mimedata-filename)


## 2.0.0 beta 1 ##
2016-03-23[^1]

##### Major Changes: #####
- correlation module now correctly included in main toolbox app (test for valid files and working dir as well as passing working dir to correlation module)
- first big file structure cleanup and GUI change from QWidget to QMainWindow for correlation module standalone mode

##### Minor Changes: #####
- fixed folder spelling ("tdtc" to "tdct")
- app icon change

##### Bugfixes: #####
- making the correlation module easily integrable into other qt apps. Therefore a few structural changes were introduced to the correlation module code


[^1]: Jan Arnold - jan.arnold@coraxx.net
