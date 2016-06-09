# Changelog #

## 2.0.3 ##
2016-06-09[^1]

##### Minor Changes: #####
- added some in-code documentation
- added missing matlab function in matlab roatation script generator
- stack processing of CorrSight sequences now include tiles. They are added in sequence, i.e. stack after stack in one file

##### Bugfixes:#####
- fixed loading of RGB images. Some were imported incorrectly and showed tiling
- coordinate offset calculation for rotation center other than 0,0,0
- matlab roatation script generator variable typo fixed

##### Known bugs:#####
- file list order from working directory in 3DCT main window not sorted correctly under Linux (tested under Ubuntu 15.04)
- when changing contrast/brightness and the focus is switched quickly during the process (like clicking on the other image) the order of added markers is not correct anymore. A workaround is to click on the affected image and change the contrast/brightness again, or reset it.


## 2.0.2 ##
2016-04-27[^1]

##### Minor Changes: #####
- removed broken deprecated poly spline method for extracting z coordinates from beads
- quick help documentation update
- added menu help link to online user's guide

##### Bugfixes:#####
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

##### Bugfixes:#####
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

##### Bugfixes:#####
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

##### Bugfixes:#####
- drop file/dir path on QLineEdit mac bug fixed (http://stackoverflow.com/questions/34689562/pyqt-mimedata-filename)


## 2.0.0 beta 1 ##
2016-03-23[^1]

##### Major Changes: #####
- correlation module now correctly included in main toolbox app (test for valid files and working dir as well as passing working dir to correlation module)
- first big file structure cleanup and GUI change from QWidget to QMainWindow for correlation module standalone mode

##### Minor Changes: #####
- fixed folder spelling ("tdtc" to "tdct")
- app icon change

##### Bugfixes:#####
- making the correlation module easily integrable into other qt apps. Therefore a few structural changes were introduced to the correlation module code


[^1]: Jan Arnold - jan.arnold@coraxx.net
