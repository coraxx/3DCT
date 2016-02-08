"""
Sorts series, fixes image headers, limits the data and calculates the dose.

# Author: Vladan Lucic (Max Planck Institute for Biochemistry)
# $Id: sort_series.py 991 2013-10-18 12:23:22Z vladan $
"""

__version__ = "$Revision: 991 $"

import logging
import numpy
import pyto

############################################################
#
# Parameters
#
##############################################################

# input series pattern
# Example: in_path = '../em-series/neu.*em' matches all files in '../em-series' 
# directory that start with 'neu' and end with 'em'. 
in_path = '../em-series/neu.*em'  

# regular expression match mode for in_path, one of the following:
#  - 'search':  (like re.search) pattern somewhere in the target string
#  - 'match': (like re.match) target string begins with the pattern
#  - 'exact': whole target string is mathed 
mode = 'exact'

# sorted series name (uses the same format as in_path)
out_path = 'neu_'

# number of digits of a projection number in the sorted series file name
out_pad = 2

# microscope type, options: 
#  - 'cm300': CM300
#  - 'polara-1_01-07': Polara 1 from 01.2007 - 12.2008
#  - 'polara-1_01-09': Polara 1 from 01.2009 - present 
#  - 'polara-2_01-09': Polara 2 from 01.2009 - present
#  - 'krios-2_falcon_05-2011': Krios 2, Falcon detector from 2011 - present
microscope = 'polara-1_01-09'

# how the image headers are fixed: None (no fixing), 'auto' (determined from
# microscope, 'polara_fei-tomo' (for polara 1 and 2 with FEI software) or
# 'cm300' (cm 300)
header_fix_mode = 'auto'

# greyscale values limits are the average plus or minus this number of std's
limit = 4

# size of the subarray used to find the replacement value for a voxel that's out
# of the limits 
size = 5

# only calculate the dose (if True parameters between out_path and size are
# not used)
dose_only = False

# print info messages
print_info = True

# print lot of info messages
print_debug = False


###########################################################
#
# Work
#
###########################################################

def main():
    """
    Main function
    """

    # determine fix_mode
    if header_fix_mode == 'auto':
        if ((microscope == 'polara-1_01-07') 
            or (microscope == 'polara-1_01-09') 
            or (microscope == 'polara-2_01-09')):
            fix_mode = 'polara_fei-tomo'
        elif microscope == 'krios-2_falcon_05-2011':
            fix_mode = 'krios_fei-tomo'
        elif microscope == 'cm300':
            fix_mode = 'cm300'
        else:
            raise ValueError("Sorry, microscope: ", microscope, 
                             " is not understood.")
    else:
        fix_mode = header_fix_mode

    # set logging
    if print_debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)s %(message)s')
    elif print_info:
        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s %(message)s')

    logging.debug('DEBUG')
    logging.info("INFO")

    if not dose_only:

        # just check the series
        in_ser = pyto.tomo.Series(path=in_path, mode=mode)
        logging.info("Checking the series:")
        logging.info('  Angle        Old name    ->     New name')
        in_ser.sort(test=True)

        # remove (manually) bad projections
        # ToDo: check the angles and complain if needed
        print('\nIf a tilt angle is repeated interrupt the procedure (Ctrl-C)')
        raw_input('and remove bad projection(s), otherwise press Return:')

        # sort and correct the series 
        logging.info("Sorting the series:")
        logging.info('  Angle        Old name    ->     New name     Mean  Std')
        in_ser.sort(
            out=out_path, pad=out_pad, fix_mode=fix_mode, 
            microscope=microscope, limit=limit, limit_mode='std', size=size)

    else:

        # dose only
        corr_ser = pyto.tomo.Series(path=in_path, mode=mode)

    # get dose for the sorted (corrected) series
    logging.info("Calculating the dose:")
    corr_ser = pyto.tomo.Series(path=in_path, mode='match')
    corr_ser.getDose(conversion=pyto.io.microscope_db.conversion[microscope])

# run if standalone
if __name__ == '__main__':
    main()
