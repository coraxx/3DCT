#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rotate original light microscope volume with tom_rotate function in matlab.

This generates the matlab script and runs in the matlab -nodisplay console.

# @Title			: matlab3Drotation
# @Project			: 3DCTv2
# @Description		: Rotate original light microscope volume
# @Author			: Jan Arnold
# @Email			: jan.arnold (at) coraxx.net
# @Copyright		: Copyright (C) 2016  Jan Arnold
# @License			: GPLv3 (see LICENSE file)
# @Credits			: Florian Beck, Max-Planck-Institute for Biochemistry
# @Maintainer		: Jan Arnold
# @Date				: 2016/01
# @Version			: 3DCT 2.0.0 module rev. 1
# @Status			: developement
# @Usage			: Meant to be imported, i.e. import matlab3Drotation.py and used with calling
# 					: matlab_rotate(img_vol,)
# @Notes			:
# @Python_version	: 2.7.11
"""
# ======================================================================================================================

import sys
import os

try:
	import matlab.engine
except Exception as e:
	print e
	sys.exit()

filein			= 'S1G2_40x_area1_1_resliced.raw'
dtype			= 'uint16'
endiantype		= 'be'
dimensions_x	= 1344
dimensions_y	= 1024
dimensions_z	= 123

fileout			= 'S1G2_40x_area1_0_resliced'

eul1_phi		= -59.561
eul1_psi		= 179.763
eul1_theta		= 77.852
scale1			= 1.199
shiftx1			= -17.608
shifty1			= -300.553

eul2_phi		= -58.581
eul2_psi		= 178.855
eul2_theta		= 27.014
scale2			= 0.898
shiftx2			= 183.565
shifty2			= -37.198

lam_start_x		= 661
lam_end_x		= 885
lam_start_y		= 512
lam_end_y		= 518

binning			= 'false'
binfactor		= 0
showfig			= 'true'
savevolrot		= 'false'
cutoutlamella	= 'true'


def genMatlabScript():
	## Generate Matlab script
	format_args = [
		filein,					# {0} = 'str'  filepath to raw volume
		dtype,					# {1} = 'str'  dtype, probably 'int16' or 'uint16'
		endiantype,				# {2} = 'str'  endian type, probably be
		dimensions_x,			# {3} = 'int'  vol in dimension x	e.g. 1344	[px]
		dimensions_y,			# {4} = 'int'  vol in dimension y	e.g. 1024	[px]
		dimensions_z,			# {5} = 'int'  vol in dimension z	e.g. 106	[px]
		fileout,				# {6} = 'str'  fileout e.g. /path/to/dir/filename without extension
		eul1_phi,				# {7} = 'int'  correlated rotation angle e.g. FIB: phi
		eul1_psi,				# {8} = 'int'  correlated rotation angle e.g. FIB: psi
		eul1_theta,				# {9} = 'int'  correlated rotation angle e.g. FIB: theta
		scale1,					# {10} = 'int'  scalingfactor e.g. FIB
		shifty1,				# {11} = 'int'  shift in y e.g. FIB
		shiftx1,				# {12} = 'int'  shift in x e.g. FIB
		eul2_phi,				# {13} = 'int'  second correlated rotation angle e.g. SEM: phi
		eul2_psi,				# {14} = 'int'  second correlated rotation angle e.g. SEM: psi
		eul2_theta,				# {15} = 'int'  second correlated rotation angle e.g. SEM: theta
		scale2,					# {16} = 'int'  second scalingfactor e.g. SEM
		shifty2,				# {17} = 'int'  second shift in y e.g. SEM
		shiftx2,				# {18} = 'int'  second shift in x e.g. SEM
		# +1 because matlab is not counting zero-based
		lam_start_x + 1,		# {19} = 'int'  lamella start x coordinate	(1)		1/3----------------2/3
		lam_end_x + 1,			# {20} = 'int'  lamella end x coordinate		(2)		 |					|
		lam_start_y + 1,		# {21} = 'int'  lamella start y coordinate	(3)		 |					|
		lam_end_y + 1,			# {22} = 'int'  lamella end y coordinate		(4)		1/4----------------2/4
		binning,				# {23} = 'str'  binning true or false
		binfactor,				# {24} = 'int'  binning factor, e.g. 1 for one time binning
		showfig,				# {25} = 'str'  showfig true or false
		savevolrot,				# {26} = 'str'  savevolrot true or false
		cutoutlamella,			# {27} = 'str'  cut out lamella part from LM data true or false
	]

	script_template = '''
function exitcode = rotate_script()

%% Variables
filein 			=  '{0}';											%% Path for input file
dtype 			=  '{1}';											%% Data type, probably 'int16' or 'uint16'
endiantype 		=  '{2}';											%% Endian type, probably be
dimensions 		=  [{3} {4} {5}];									%% dimensions of file in

fileout 		=  '{6}';											%% Path for output file without suffix	string

eulerangle 		=  [{7} {8} {9}]									%% Correlation rotation angle (Phi Psi Theta)
scale 			=  {10};											%% Correlation scaling factor
shiftxy 		= [{11} {12}];										%% Correlation shift in y,x (tom_shift needs [dy dx])

eulerangle_col 	= [{13} {14} {15}]									%% Second correlation rotation angle for lamella cut out (Phi Psi Theta)
scale_col 		=  {16};											%% Second scale for lamella cut out
shiftxy_col 	= [{17} {18}];										%% Second correlation shift in y,x for lamella cut out (tom_shift needs [dy dx])

lam_start_x 	=  {19};											%% Lamella x axes start coordinate in original e.g. FIB image
lam_end_x 		=  {20};											%% Lamella x axes end coordinate in original e.g. FIB image
lam_start_x 	=  {21};											%% Lamella y axes start coordinate in original e.g. FIB image
lam_end_x 		=  {22};											%% Lamella y axes end coordinate in original e.g. FIB images

%% binning and show figure options
binning 		=  {23};											%% Binning								true|false
binfactor 		=  {24};											%% binning factor. 0 for no binning
showfig 		=  {25};											%% Show figures of images				true|false
savevolrot 		=  {26};											%% Save rotated vol as em file			true|false
cutoutlamella 	=  {27};											%% Cut out lamella						true|false

%% load raw
vol = tom_rawread(filein,dtype,endiantype,dimensions,0,0);			%% Dimensions x,y,z

%% reduce size by changing datatype from float to single
vol = single(vol);

if binning == true
	vol = csbin(vol,binfactor,3);
	vol = single(vol);
else
	binfactor = 0;
end

vol = quadvol(vol,0);
vol = tom_rotate(vol,eulerangle);									%% Phi Psi Theta

if showfig == true
	figure; imshow(tom_norm(max(vol,[],3),1)');
end

if savevolrot == true
	tom_emwrite(strcat(fileout,'_rot.em'),vol);
end

im = tom_norm(max(vol,[],3),1)';
imwrite(im,strcat(fileout,'_max.tif'));
im = imresize(im,scale);											%% scaling factor
im_shift = tom_shift(im, shiftxy/(2^binfactor));					%% shift x y
if showfig == true
	figure; imshow(im_shift);
end
imwrite(im_shift,strcat(fileout,'_max_scale_shift.tif'));

%%%%%%%%%%%%%%%%%%%
%% cut out lamella
if cutoutlamella == true
	[euler_out shift_out rott]=tom_sum_rotation([-eulerangle(2) -eulerangle(1) -eulerangle(3); ...
												eulerangle_col(1) eulerangle_col(2) eulerangle_col(3)],[0 0 0; 0 0 0]);

	vol(1:(1/scale * (lam_start_x + -shiftxy(1))/(2^binfactor)),:,:)=0;	%% x axes from 0 to beginning of lamella
	vol((1/scale * (lam_end_x + -shiftxy(1))/(2^binfactor)):end,:,:)=0;	%% x axes from end of lamella to end of end of volume
	vol(:,1:(1/scale * (lam_start_y + -shiftxy(2))/(2^binfactor)),:)=0;	%% y axes from 0 to beginning of lamella
	vol(:,(1/scale * (lam_end_y + -shiftxy(2))/(2^binfactor)):end,:)=0;	%% y axes from end of lamella to end of end of volume


	im = tom_norm(max(vol,[],3),1)';
	if showfig == true
		figure; imshow(im);
	end
	imwrite(im,strcat(fileout,'_max_cut_FIB.tif'));
	im = imresize(im,scale);											%% First scaling factor
	im_shift = tom_shift(im, shiftxy/(2^binfactor));					%% First shift x y
	imwrite(im_shift,strcat(fileout,'_max_cut_FIB_scale_shift.tif'));

	vol = tom_rotate(vol,euler_out);

	im = tom_norm(max(vol,[],3),1)';
	if showfig == true
		figure; imshow(im);
	end
	imwrite(im,strcat(fileout,'_max_cut_SEM.tif'));
	im = imresize(im,scale_col);										%% Second scaling factor
	im_shift = tom_shift(im, shiftxy_col/(2^binfactor));				%% Second shift x y
	imwrite(im_shift,strcat(fileout,'_max_cut_SEM_scale_shift.tif'));
end

exitcode = 0

'''
	return script_template.format(*format_args)


def writeScript():
	file = open("rotate_script.m", "w")
	file.write(genMatlabScript())
	file.close()


def runMatlab():
	writeScript()
	eng = matlab.engine.start_matlab()
	exitcode = eng.rotate_script()
	if exitcode == 0:
		print "Script successfully executed"
	else:
		print "Something went horribly wrong!!!11 AAAAAHHHHHHHHH"
	cleanUp()


def cleanUp():
	os.remove("rotate_script.m")

if __name__ == "__main__":
	writeScript()
	cleanUp()
