#!/usr/bin/env python
"""

IMPORTANT: probably doesn't work, needs to be updated to reflect changes in connections.py 

Makes segmentation based on threshold and connectivity, and finds connections
(segments) that contact specified boundaries.

Useful for connections between many boundaries of the same kind, such as
synaptic vesicles.

This script may be placed anywhere in the directory tree.

$Id$
Author: Vladan Lucic 
"""
__version__ = "$Revision$"

import os
import os.path
import time
import numpy
import pyto


##############################################################
#
# Parameters
#
##############################################################

############################################################
#
# Image (grayscale) file. If it isn't in em or mrc format, format related
# variables (shape, data type, byte order and array order) need to be given
# (see labels file section below).
#

# name of the image file
image_file_name = "../3d/tomo.em"

###############################################################
#
# Labels file, specifies boundaries and possibly other regions. If the file
# is in em or mrc format shape, data type, byte order and array order are not
# needed (should be set to None). If these variables are specified they will # override the values specified in the headers.
#

# name of the labels file (file containing segmented volume) 
labels_file_name = "labels.dat"

# use this if multiple labels files are used (all need to have same format)
#labels_file_name = ("labels_1.dat", "labels_2.dat", "labels_3.dat")

# id shift in each subsequent labels (in case of multiple labels files) 
#shift = None     # shift is determined automatically
shift = 254

# labels file dimensions
labels_shape = (100, 120, 90)

# labels file data type (e.g. 'int8', 'int16', 'int32', 'float16', 'float64') 
labels_data_type = 'int8'

# labels file byteOrder ('<' for little-endian, '>' for big-endian)
labels_byte_order = '<'

# labels file array order ('FORTRAN' for x-axis fastest, 'C' for z-axis fastest)
labels_array_order = 'FORTRAN'

# offset of labels in respect to the data (None means 0-offset)
labels_offset = None

###########################################################
#
# Segmentation parameters
#

# If True connections are read from connections file(s) (the name(s) is/are
# specified in the connections file segment, below). If False, connections
# are obtained by segmentation (labeling) of the image. 
read_connections = False

# threshold
threshold = numpy.arange(-0.02, -0.09, 0.02)

# connectivity of the structuring element used for segment determination (can be 1-4)
# Not used if read_connections is True.
struct_el_connectivity = 1 

###########################################################
#
# Boundaries and other segments in labels
#

# ids of all segments corresponding to all labels files. Can use individual ids,
# None (all ids) and range.
# The following means ids 2, 3 and 6 from labels_1, all ids from labels_2 and
# ids 3, 4, ... 8 from labels_3
all_ids = ([2,3,6], None, range(3,9))

# ids of all boundaries. All formats available for all_ids are accepted here also.
# In addition, nested list can be used where ids in a sublist are uderstood in the
# "or" sense, that is all boundaries listed in a sublist form effectivly a single
# boundary. However, nested lists can be used within one labels file only.
# The following means there are 11 boundaries: 2, 3 and 5 from labels_1, combined
# 7 and 8 and combined 9 and 10 from lables_2 and 3, 4, ... 8 from labels_3.  
boundary_ids = ([2,3,6], [[7,8], [9,10]], range(3,9))  

# number of boundaries that each segment is required to contact
n_boundary = 2

# 'exact' to require that segments contact exactly n_boundary boundaries, or
# 'at_least' to alow n_boundary or more contacted boundaries 
count_mode = 'at_least'

# id of region where connections can be formed. Use 0 unles you know what you're doing.
# Not used if read_connections is True.
conn_region = 0

# Connections are formed in the area surrounding boundaries (given by all ids
# specified in boundary_ids) that are not further than free_size from the
# boundaries and that are still within conn_region. If free_size = 0, the area
# surrounding boundaries is maximaly extended (to the limits of conn_region)
# Not used if read_connections is True.
free_size = 10  # the same for all boundaries
#free_size = [10, 12, 15, 12, 10] # one for each boundary from all labels files

# Defines the manner in which the areas surrounding individual boundaries are
# combined. These areas can be added (free_mode='add') or intersected
# (free_mode='intersect'). Not used if read_connections is True. 
free_mode = 'add'

# If None, the region where the connections are made is determined by using all
# boundaries together. Alternatively, if an iterable of lists is
# given the segmentation is done in a free region established between
# (usually two) boundaries given in each element of this list.
# Note: not sure if it works, use None
#boundary_lists = pyto.util.probability.combinations(elements=boundary_ids,
#                                                   size=n_boundary,
#                                                   repeat=False, order=False)
# simpler version of the above
#boundary_lists = [(2,3), (2,6), (3,6)]
boundary_lists = None

###########################################################
#
# Connections file. The results file name is formed as:
#
#   <conn_directory>/<conn_prefix> + image root + _tr-<threshold> + <conn_suffix>
#

# connections directory
conn_directory = ''

# connections file name prefix (no directory name)
conn_prefix = ''

# include image file root (filename without directory and extension)
insert_root_conn = True

# connections file name suffix
conn_suffix = ".em"

# connections data type, 'uint8' , or
# conn_data_type = 'uint8'        # if max segment id is not bigger than 255
conn_data_type = 'uint16'         # more than 255 segments

############################################################
#
# Output (results) file. The results file name is formed as:
#
#   <res_directory>/<res_prefix> + labels root + _tr-<threshold> + <res_suffix>
#

# results directory
res_directory = ''

# results file name prefix (without directory)
res_prefix = ''

# include image file root (filename without directory and extension)
insert_root_res = True

# results file name suffix
res_suffix = "_con.dat"

# include total values (for all segments taken together) in the results, id 0
include_total = True


################################################################
#
# Work
#
################################################################

###########################################
#
# Read image and segment files
#

# read image file
image_file = pyto.io.ImageIO()
image_file.read(file=image_file_name)
image = pyto.segmentation.Image(data=image_file.data)

# read labels (boundary) file
if isinstance(labels_file_name, str):
    labels_file_name = (labels_file_name,)
    all_ids = (all_ids,)
    boundary_ids = (boundary_ids,)
bound = pyto.segmentation.Segment()
curr_shift = 0
new_b_ids = []
for (l_name, ids, b_ids) in zip(labels_file_name, all_ids, boundary_ids):
    labels = pyto.io.ImageIO()
    labels.read(file=l_name, byteOrder=labels_byte_order, dataType=labels_data_type,
            arrayOrder=labels_array_order, shape=labels_shape)
    curr_bound = pyto.segmentation.Segment(data=labels.data, ids=ids)
    bound.add(new=curr_bound, shift=curr_shift)
    new_b_ids.extend(pyto.util.nested.add(curr_shift, b_ids))
    if shift is None:
        curr_shift = None
    else:
        curr_shift += shift
bound.setOffset(labels_offset)

############################################
#
# Stuff that need to be done once
#

# extract root from the image_file_name
(dir, base) = os.path.split(image_file_name)
(root, ext) = os.path.splitext(base)

##########################################
#
# Thresholding and connectivity analysis
#

# loop over thresholds
for tr in threshold:
    seg = pyto.segmentation.Segment()

    # determine connections file name 
    if insert_root_conn:
        conn_base = conn_prefix + root + "_tr-" + str(tr) + conn_suffix
    else:
        conn_base = conn_prefix + "_tr-" + str(tr) + conn_suffix
    conn_file_name = os.path.join(conn_directory, conn_base)

    # get connections and analyze them
    if read_connections:

        # read conections from a file
        conn_file = pyto.io.ImageIO()
        conn_file.read(conn_file_name)

        # analyze connections
        seg.connectivity(input=conn_file.data, boundary=bound,
                         boundaryIds=boundary_ids, boundaryLists=boundary_lists,
                         label=False,
                         nBoundary=n_boundary, countMode=count_mode, update=True)

    else:

        # threshold
        input = image.doThreshold(threshold=tr, pickDark=True) 

        # determine and analyze connections
        seg.setStructEl(connectivity=struct_el_connectivity)        
        seg.connectivity(input=input, boundary=bound,
                         boundaryIds=boundary_ids, boundaryLists=boundary_lists,
                         mask=conn_region, freeSize=free_size, freeMode=free_mode,
                         nBoundary=n_boundary, countMode=count_mode, update=True)

    # get density stats
    dens = pyto.segmentation.Statistics(data=image.data, labels=seg.data,
                                        ids=seg.ids)
    dens.calculate()

    # calculate morphology
    mor = pyto.segmentation.Morphology(segments=seg.data)
    mor.getVolume()
    mor.getSurface()

    ############################################
    #
    # Write connections and results files
    #

    # make connections 
    if (not_read_connections) and (len(seg.ids) > 0):
        conn_file = pyto.io.ImageIO()
        conn_file.write(file=conn_file_name, data=seg.data, dataType=conn_data_type)

    # make results file name and open the results file
    if insert_root_res:
        resBase = res_prefix + root + "_tr-" + str(tr) + res_suffix
    else:
        resBase = res_prefix + "_tr-" + str(tr) + res_suffix
    res_file_name = os.path.join(res_directory, resBase)
    res_file = open(res_file_name, 'w')

    # results file header
    image_time = \
        '(' + time.asctime(time.localtime(os.path.getmtime(image_file_name))) + ')'
    labels_time = [time.asctime(time.localtime(os.path.getmtime(l_file))) \
                 for l_file in labels_file_name]
    labels_name_time = [fi + ' (' + ti + ') ' \
                        for (fi, ti) in zip(labels_file_name, labels_time)] 
    conn_time = time.asctime(time.localtime(os.path.getmtime(conn_file_name)))
    header = ("#",
        "# Image: " + image_file_name + " " + image_time,
        "# Boundaries: " + str(tuple(labels_name_time)),
        "# Connections (" + in_out + "): " + conn_file_name + "(" + conn_time + ")",
        "# Working directory: " + os.getcwd(),
        "#",
        "# Boundary ids: " + str(boundary_ids),
        "# Boundary ids, shifted: " + str(new_b_ids,
        "# Number of boundaries contacted: " + str(n_boundary),
        "# Contact mode: " + count_mode,
        "#",
        "# Connection region: " + str(conn_region),
        "# Free region size: " + str(free_size),
        "# Free region mode: " + free_mode,
        "#",
        "# Threshold: " + str(tr),
        "#",
        "# Structuring element:",
        "#   - connectivity: " + str(seg.structEl.connectivity),
        "#   - size: " + str(seg.structEl.size),
        "#")
    for line in header: res_file.write(line + os.linesep)

    # write results table head
    tabHead = ["# Id        Density              Volume Surface   Boundaries ",
               "#      mean   std    min    max" ]
    for line in tabHead: res_file.write(line + os.linesep)

    # write the results
    outVars = [ dens.mean, dens.std, dens.min, dens.max, mor.volume, mor.surface ]
    outFormat = ' %3u %6.2f %5.2f %6.2f %6.2f %6u %6u '
    resTable = pyto.io.util.arrayFormat(arrays=outVars, format=outFormat,
                                        indices=seg.ids, prependIndex=True)
    for (sid, line) in zip(seg.ids, resTable):
        boundIds = numpy.array2string(seg.contacts.findBoundaries(segmentIds=sid,
                                                                 nSegment=1))
        res_file.write(line + "    %s" % boundIds + os.linesep)

    # write results for all connections together
    if include_total:
        tot_line = pyto.io.util.arrayFormat(arrays=outVars, format=outFormat,
                                            indices=[0], prependIndex=True)
        res_file.write(os.linesep + tot_line[0] + os.linesep)

    res_file.flush()
