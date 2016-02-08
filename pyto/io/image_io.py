"""
Contains class ImageIO for image file read/write.

# Author: Vladan Lucic (Max Planck Institute for Biochemistry)
# $Id: image_io.py 1103 2014-12-29 11:36:27Z vladan $
"""

__version__ = "$Revision: 1103 $"

import sys
import struct
import re
import os.path
import logging
from copy import copy, deepcopy

import numpy
import scipy
import scipy.ndimage as ndimage

from local_exceptions import FileTypeError
import microscope_db

class ImageIO(object):
    """
    Reads and writes EM image files in em, mrc and raw formats.

    An image file in em or mrc format can be read in the following way:

      myImage = ImageIO()
      myImage.read(file='my_file.em')

    ow written as:

      myImage = ImageIO()
      myImage.write(file='my_file.em', data=my_array, header=my_header)

    Raw file reading and writting is the same except that more arguments are
    required to read (see self.read).

    Important attributes:
      - self.fileName: file name
      - self.file_: file instance
    """


    ##########################################################
    #
    # Initialization
    #
    #########################################################

    # determine machine byte order
    byte_order = sys.byteorder
    if byte_order == 'big':
        machineByteOrder = '>'
    elif byte_order == 'little':
        machineByteOrder = '<'
    else:
        machineByteOrder = '<'
        logging.warning("Machine byte order could not be determined, set to "\
                            + " '<' (little endian).")

    def __init__(self, file=None):
        """
        Initializes variables.

        Sets self.fileName to file if file is a string, or sets self.file_ to
        file if file is a file instance.
        """


        # initialize attributes
        self.byteOrder = None
        self.defaultArrayOrder = 'C'
        self.arrayOrder = None
        self.dataType = None
        self.shape = None
        self.data = None
        self.axisOrder = None
        self.length = None
        self.pixel = None
        
        self.mrcHeader = None
        self.emHeader = None
        self.rawHeader = None
        self.header = None
        self.rawHeaderSize = None

        # parse arguments
        if file is not None:
            if isinstance(file, str):
                self.fileName = file
            elif isinstance(file, file):
                self.file_ = file
        
        return
    
    ##########################################################
    #
    # General image file read and write
    #
    #########################################################

    # File formats and extensions
    fileFormats = { 'em': 'em',
                    'EM': 'em',
                    'raw': 'raw',
                    'dat': 'raw',
                    'RAW': 'raw',
                    'mrc': 'mrc',
                    'rec': 'mrc'
                   }

    def read(self, file=None, fileFormat=None, byteOrder=None, dataType=None,
             arrayOrder=None, shape=None):
        """
        Reads image file in em, mrc or raw data formats and saves the
        data in numpy.array format.

        For reading em and mrc files (having correct extension) only file
        argument is necessary:

          image = Image()
          image.read(file='myfile.em')

        Alternatively, file name can be given in the constructor:

          image = Image(file='myfile.em')
          image.read()

        If other arguments are given they will override the corresponding
        values obtained form image header (use if you know what you're
        doing).

        For reading raw files, arguments dataType and shape need to
        be specified:

          read(file='myfile.raw', dataType='float32', shape=(200,150,70))

        By default, arguments byteOrder='<' (little-endian) and
        arrayOrder='FORTRAN'.

        File format is determined from the extension (em, mrc or raw). This
        can be overriden by specifying fileFormat argument.

        Arguments:
          - file: file name
          - fileFormat: 'em', 'mrc', or 'raw'
          - byteOrder: '<' (little-endian), '>' (big-endian)
          - dataType: any of the numpy types, e.g.: 'int8', 'int16', 'int32',
            'float32', 'float64'
          - arrayOrder: 'C' (z-axis fastest), or 'FORTRAN' (x-axis fastest)
          - shape: (x_dim, y_dim, z_dim), needs to be compatible with the
          data read

        Sets the following attributes (in addition to the arguments):
          - data: data in numpy.array form
          - emHeader / mrcHeader: tuple of all header values (em/mrc) files
          - header: emHeader for em file, mrcHeader for mrc file or raw header
          for raw file
          - headerString: string containing a header

        Alternatively, any argument can be omitted if an attribute of the
        same name is set.         
        """

        # determine the file format
        self.setFileFormat(file_=file, fileFormat=fileFormat)
        if self.fileFormat is None:
            raise FileTypeError(requested=self.fileFormat,
                                defined=self.fileFormats)

        # call the appropriate read method
        if self.fileFormat == 'em':
            self.readEM(file=file, byteOrder=byteOrder, shape=shape,
                         dataType = dataType, arrayOrder=arrayOrder)
            self.header = self.emHeader
        elif self.fileFormat == 'mrc':
            self.readMRC(file=file, byteOrder=byteOrder, shape=shape,
                         dataType = dataType, arrayOrder=arrayOrder)
            self.header = self.mrcHeader
        elif self.fileFormat == 'raw':
            self.readRaw(file=file, byteOrder=byteOrder, dataType=dataType,
                         arrayOrder=arrayOrder, shape=shape)
            self.header = self.rawHeader
        else: raise FileTypeError(requested=self.fileFormat,
                                  defined=self.fileFormats)

        return

    def readHeader(self, file=None, fileFormat=None, byteOrder=None):
        """
        Reads heder of an image file in em, mrc or raw data formats. 
        """
        
        # determine the file format
        self.setFileFormat(file_=file, fileFormat=fileFormat)
        if self.fileFormat is None:
            raise FileTypeError(requested=self.fileFormat,
                                defined=self.fileFormats)

        # call the appropriate read method
        if self.fileFormat == 'em':
            self.readEMHeader(file=file, byteOrder=byteOrder)
        elif self.fileFormat == 'mrc':
            self.readMRCHeader(file=file, byteOrder=byteOrder)
        elif self.fileFormat == 'raw':
            self.rawHeader = ''
        else: raise FileTypeError(requested=self.fileFormat,
                                  defined=self.fileFormats)

        return

    def write(self, file=None, data=None, fileFormat=None, byteOrder=None,
              dataType=None, arrayOrder=None, shape=None, length=None, 
              pixel=None, header=None, extended=None, casting='unsafe'):
        """
        Writes image file (header if applicable and data).

        Values of all non-None arguments are saved as properties with same 
        names.

        If fileFormat is not given it is determined from the file extension.

        Data (image) has to be specified by arg data or previously set 
        self.data attribute.

        Data type and shape are determined by args dataType and shape, 
        previously set attributes self.dataType and self.shape, or by the data 
        type and shape of the data, in this order.

        If data type (determined as described above) is not one of the 
        data types used for the specified file format (ubyte, int16, float32, 
        complex64 for mrc and uint8, uint16, int32, float32, float64, 
        complex64 for em), then the value of arg dataType has to be one of the 
        appropriate data types. Otherwise an exception is raised.

        If data type (determined as described above) is different from the 
        type of actual data, the data is converted to the data type. Note that
        if these two types are incompatible according to arg casting, an 
        exception is raised. 

        Values for byteOrder and arrayOrder are set to the first value found 
        from the arguments, properties with same names, or from emHeader / 
        mrcHeader default values. 

        If data is not given, only a header is writen.

        Additional header parameters are determined for mrc format. Nxstart, 
        nystart and nzstart are set to 0, while mx, my and mz to the 
        corresponding data size (grid size). xlen, ylen and zlen are taken from
        arg length if given, or obtained by multiplying data size with pixel 
        size (in nm).

        Arguments:
          - file: file name
          - data: (ndarray) image 
          - fileFormat: 'em', 'mrc', or 'raw'
          - byteOrder: '<' (little-endian), '>' (big-endian)
          - dataType: any of the numpy types, e.g.: 'int8', 'int16', 'int32',
            'float32', 'float64'
          - arrayOrder: 'C' (z-axis fastest), or 'FORTRAN' (x-axis fastest)
          - shape: (x_dim, y_dim, z_dim)
          - length: (list aor ndarray) length in each dimension in nm (used 
          only for mrc format)
          - pixel: pixel size in nm (used only for mrc format if length is 
          None)
          - header: (list) image header
          - extended: (str) extended header string, only for mrc 
          - casting: Controls what kind of data casting may occur: 'no', 
          'equiv', 'safe', 'same_kind', 'unsafe'. Identical to numpy.astype()
          method.
        """

        # determine the file format 
        self.setFileFormat(file_=file, fileFormat=fileFormat)
        if self.fileFormat is None:
            raise FileTypeError(requested=self.fileFormat,
                                defined=self.fileFormats)

        # call the appropriate write method
        if self.fileFormat  == 'em':
            self.writeEM(
                file=file, data=data, header=header, byteOrder=byteOrder,
                dataType=dataType, arrayOrder=arrayOrder, shape=shape,
                casting=casting)
        elif self.fileFormat  == 'mrc':
            self.writeMRC(
                file=file, data=data, header=header, byteOrder=byteOrder,
                dataType=dataType, arrayOrder=arrayOrder, shape=shape, 
                length=length, pixel=pixel, extended=extended, casting=casting)
        elif self.fileFormat == 'raw':
            self.writeRaw(
                file=file, data=data, header=header, byteOrder=byteOrder,
                dataType=dataType, arrayOrder=arrayOrder, shape=shape, 
                casting=casting)
        else:
            raise FileTypeError(requested=self.fileFormat, 
                                defined=self.fileFormats)

        return self.file_

    ###########################################################
    #
    # EM format
    #
    ###########################################################

    # EM file format properties
    em = { 'headerSize': 512,
           'headerFormat': '4b 3i 80s 40i 20s 8s 228s',
           'defaultByteOrder': machineByteOrder,
           'arrayOrder': 'FORTRAN'
                 }
    emHeaderFields = (
        'machine', 'newOS9', 'noHeader', 'dataTypeCode', 'lengthX', 'lengthY',
        'lengthZ', 'comment',
        'voltage', 'cs', 'aperture', 'magnification', 'postmagnification',
        'exposureTime','_pixelsize', 'emCode', 'ccdPixelsize', 'ccdLength',
        'defocus', 'astigmatism', 'astigmatismAngle', 'focusIncrement',
        'countsPerelectron',
        'intensity', 'energySlitWidth', 'energyOffset', '_tiltAngle', 
        'tiltAxis',
        'field_21', 'field_22', 'field_23', 'markerX', 'markerY',
        'resolution', 'density', 'contrast', 'field_29', 'massCentreX',
        'massCentreY', 'massCentreZ', 'height', 'field_34',
        'widthDreistrahlbereich',
        'widthAchromRing', 'lambda', 'deltaTheta', 'field_39', 'field_40',
        'username', 'date', 'userdata')
    emDefaultHeader = [6, 0, 0, 0, 1, 1, 1, 80*' '] \
                      + numpy.zeros(40, 'int8').tolist() \
                      + [20*' ', 8*' ', 228*' ']
    emDefaultShape = [0, 0, 0]
    #emDefaultDataType = 0
    emByteOrderTab = { 5: '>',  # Mac
                       6: '<'   # PC (Intel)
                       }
    emByteOrderTabInv = dict( zip(emByteOrderTab.values(),
                                  emByteOrderTab.keys()) )
    emDataTypeTab = {1: 'uint8',
                     2: 'uint16',
                     4: 'int32',
                     5: 'float32',
                     8: 'complex64',
                     9: 'float64'
                     }
    emDataTypeTabInv = dict( zip(emDataTypeTab.values(),
                                  emDataTypeTab.keys()) )
    
        
    def readEM(self, file=None, byteOrder=None, dataType=None,
               arrayOrder=None, shape=None):
        'Reads EM file.'
        
        # open the file if needed
        self.checkFile(file_=file, mode='r')

        # set defaults
        self.arrayOrder = ImageIO.em['arrayOrder']
 
        # parse arguments
        if byteOrder is not None: self.byteOrder = byteOrder
        if dataType is not None: self.dataType = dataType
        if arrayOrder is not None: self.arrayOrder = arrayOrder
        if shape is not None: self.shape = shape

        # use defaults if needed
        if self.byteOrder is None:
            self.byteOrder = ImageIO.em['defaultByteOrder']
        if self.arrayOrder is None:
            self.arrayOrder = ImageIO.em['arrayOrder']

        # read the header
        self.readEMHeader(file=self.file_)

        # read the data
        self.readData(shape=shape)

        return

    def readEMHeader(self, file=None, byteOrder=None):
        'Reads a header of an EM file'

        # open the file if needed
        self.checkFile(file_=file, mode='r')

        # read the header
        self.headerString = self.file_.read(ImageIO.em['headerSize'])

        # determine byte order
        if byteOrder is not None:  # explicit byte order
            self.byteOrder = byteOrder
        else:                   # determine byte order form the file
            (self.machine, tmp) = struct.unpack('b 511s', self.headerString)
            self.byteOrder = ImageIO.emByteOrderTab[self.machine]
        format = self.byteOrder + ImageIO.em['headerFormat']
 
        # unpack the header with the right byte order
        self.emHeader = list( struct.unpack(format, self.headerString) )

        # parse data type and shape (important)
        self.dataType = ImageIO.emDataTypeTab[ self.emHeader[3] ]
        self.shape =  self.emHeader[4:7]

        # parse the rest of the header
        for (attr, val) in zip(ImageIO.emHeaderFields, self.emHeader):
            self.__dict__[attr] = val 

        return

    def writeEM(self, file=None, header=None, byteOrder=None, shape=None,
                dataType=None, arrayOrder=None, data=None, casting='unsafe'):
        """
        Writes EM file (header and data).

        File can be a file name (string) or an instance of file. If not given
        self.fileName determines the file name.

        Values of all non-None arguments are saved as properties with same 
        names.

        Data (image) has to be specified by arg data or previously set 
        self.data attribute.

        Data type and shape are determined by args dataType and shape, 
        previously set attributes self.dataType and self.shape, or by the data 
        type and shape of the data, in this order.

        If data type (determined as described above) is not one of the em
        data types (uint8, uint16, int32, float32, float64, complex64), then
        the value of arg dataType has to be one of the em data types. Otherwise
        an exception is raised.

        If data type (determined as described above) is different from the 
        type of actual data, the data is converted to the data type. Note that
        if these two types are incompatible according to arg casting, an 
        exception is raised. 

        Values for byteOrder and arrayOrder are set to the first value found 
        from the arguments, properties with same names, from emHeader of 
        default values. 

        If data is not given, only a header is written.
        """

        # open the file if needed
        self.checkFile(file_=file, mode='w')

        # set emHeader
        if header is not None: 
            self.emHeader = header

        # byteOrder: use the argument, self.byteOrder, or the default value
        if byteOrder is not None: self.byteOrder = byteOrder
        if self.byteOrder is None:
            #if self.emHeader is not None:
            #    self.byteOrder = ImageIO.emByteOrderTab[self.emHeader[0]]
            #else:
            self.byteOrder = ImageIO.em['defaultByteOrder']

        # arrayOrder: use the argument, self.arrayOrder, or the default value
        if arrayOrder is not None: self.arrayOrder = arrayOrder
        if self.arrayOrder is None:
            self.arrayOrder = ImageIO.em['arrayOrder']

        # data: use the argument or the self.data, set self.shape and 
        # self.dataType
        if data is not None:
            self.setData(data, shape=shape)
        
        # dataType: use the argument or self.dataType
        if dataType is not None: 
            self.dataType = dataType
        #if self.dataType is None:
        #    self.dataType = self.emDefaultDataType
        #if self.dataType is None:
            #if self.emHeader is not None:
            #    self.dataType = ImageIO.emDataTypeTab[self.emHeader[3]]

        # convert data to another dtype if needed
        wrong_data_type = False
        try:
            if self.dataType == 'uint8':
                if self.data.dtype.name != 'uint8':
                    self.data = self.data.astype(dtype='uint8', casting=casting)
            elif self.dataType == 'uint16':
                if self.data.dtype.name != 'uint16':
                    self.data =  self.data.astype(dtype='uint16', 
                                                  casting=casting)
            elif self.dataType == 'int32':
                if self.data.dtype.name != 'int32':
                    self.data =  self.data.astype(dtype='int32', 
                                                  casting=casting)
            elif self.dataType == 'float32':
                if self.data.dtype.name != 'float32':
                    self.data = self.data.astype(dtype='float32', 
                                                 casting=casting)
            elif self.dataType == 'complex64':
                if self.data.dtype.name != 'complex64':
                    self.data = self.data.astype(dtype='complex64', 
                                                 casting=casting)
            elif self.dataType == 'float64':
                if self.data.dtype.name != 'float64':
                    self.data = self.data.astype(dtype='float64', 
                                                 casting=casting)
            else:
                wrong_data_type = True
        except TypeError:
            print("Error most likely because trying to cast " +  
                  self.data.dtype.name + " array to " + self.dataType +
                  " type. This may cause errors, so change argument dataType "
                  "to an appropriate one.")
            raise
        if wrong_data_type:
            raise TypeError(
                "Data type " + self.dataType + " is not valid for EM"
                " format. Allowed types are: " 
                + str(ImageIO.emDataTypeTab.values()))


        # shape: use the argument, self.shape, or use default
        #if shape is not None: self.shape = shape
        # probably not needed (15.01.08)
        #if self.shape is None:
        #    if self.emHeader is not None:
        #        self.shape = self.emHeader[4:8]
        #    else:
        if self.shape is None:
            self.shape = copy(ImageIO.emDefaultShape)

        # use self.emHeader or the default em header 
        if self.emHeader is None: 
            self.emHeader = copy(ImageIO.emDefaultHeader)

        # add byteOrder, dataType and shape to the header 
        try: 
            self.emHeader[0] = ImageIO.emByteOrderTabInv[self.byteOrder]
            try:
                self.emHeader[3] = ImageIO.emDataTypeTabInv[self.dataType]
            except KeyError:
                print("Data type " + self.dataType 
                      + " is not valid for EM format."
                      + "Allowed types are: " 
                      + str(ImageIO.emDataTypeTab.values()))
                raise
            for k in range( len(self.shape) ): 
                self.emHeader[4+k] = self.shape[k]
        except (AttributeError, LookupError):
            print "Need to specify byte order, data type \
            and shape of the data."
            raise

        # convert emHeader to a string and write it
        self.headerString = struct.pack(ImageIO.em['headerFormat'],
                                        *tuple(self.emHeader))
        self.file_.write(self.headerString)

        # write data if exist
        if self.data is not None: self.writeData()
        self.file_.flush()
        
        return
    
    
    #####################################################
    #
    # MRC format
    #
    #####################################################
    
    # MRC file format properties
    mrc = { 'headerSize': 1024,
           'headerFormat': '10i 6f 3i 3f 2i h 30s 4h 6f 6h 12f i 800s',
            'defaultByteOrder': machineByteOrder,
            'defaultArrayOrder': 'FORTRAN',
            'defaultAxisOrder': (1,2,3)
            }
    mrcDefaultShape = [1,1,1]
    mrcDefaultPixel = [1,1,1]
    mrcDefaultHeader = (
        numpy.ones(3, 'int32').tolist() 
        + numpy.zeros(7, 'int32').tolist() 
        + numpy.zeros(6, 'float32').tolist() 
        + list( mrc['defaultAxisOrder'] ) 
        + numpy.zeros(3, 'float32').tolist() 
        + numpy.zeros(2, 'int32').tolist() 
        + numpy.zeros(1, 'int16').tolist() 
        + [30*' '] 
        + numpy.zeros(4, 'int16').tolist() 
        + numpy.zeros(6, 'float32').tolist() 
        + numpy.zeros(6, 'int16').tolist() 
        + numpy.zeros(12, 'float32').tolist() 
        + numpy.zeros(1, 'int32').tolist() 
        + [800*' '])   
    
    # type 3 not implemented, added imod type 6
    mrcDataTypeTab = {0: 'ubyte',  
                      1: 'int16',
                      2: 'float32',
                      4: 'complex64',
                      6: 'uint16'
                     }
    mrcDataTypeTabInv = dict( zip(mrcDataTypeTab.values(),
                                  mrcDataTypeTab.keys()) )
    
    def readMRC(self, file=None, byteOrder=None, dataType=None,
                arrayOrder=None, shape=None):
        'Reads mrc file.'
        
        # open the file if needed
        self.checkFile(file_=file, mode='r')

        # parse arguments
        if byteOrder is not None: self.byteOrder = byteOrder
        if dataType is not None: self.dataType = dataType
        if arrayOrder is not None: self.arrayOrder = arrayOrder
        if shape is not None: self.shape = shape
        
        # use defaults if needed
        if self.byteOrder is None:
            self.byteOrder = ImageIO.mrc['defaultByteOrder']
        if self.arrayOrder is None:
            self.arrayOrder = ImageIO.mrc['defaultArrayOrder']

        # read the header
        self.readMRCHeader(file=self.file_)
        
        # read the data
        self.readData(shape=shape)

        return

    def readMRCHeader(self, file=None, byteOrder=None):
        """
        Reads a header of an mrc file.

        Sets attributes:
          - headerString
          - mrcHeader
          - byteOrder
          - shape
          - dataType
          - axisOrder
          - pixel: pixel size in nm
          - length: linght in all dimensions in nm
        """

        # open the file if needed
        self.checkFile(file_=file, mode='r')

        # parse arguments and set variables
        if byteOrder is not None: self.byteOrder = byteOrder
        if self.byteOrder is None:
            self.byteOrder = ImageIO.mrc['defaultByteOrder']

        # read the header
        format = self.byteOrder + ImageIO.mrc['headerFormat']
        self.headerString = self.file_.read(ImageIO.mrc['headerSize'])

        # unpack the header with the right byte order
        self.mrcHeader = list( struct.unpack(format, self.headerString) )

        # parse header
        self.parseMRCHeader()

    def parseMRCHeader(self, header=None):
        """
        Parse mrc header. If arg header is None, self.mrcHeader is used.
        """

        if header is not None:
            self.mrcHeader = header

        # parse shape and data type
        self.shape =  self.mrcHeader[0:3]  # C: z fastest changing
        self.dataType = ImageIO.mrcDataTypeTab[ self.mrcHeader[3] ]
        self.axisOrder = self.mrcHeader[16:19]  # read but not used

        # pixel size and length
        self.pixel = [0,0,0]
        for ind in [0,1,2]:
            try:
                self.pixel[ind] = (float(self.mrcHeader[ind+10]) 
                                   / self.mrcHeader[ind])
            except ZeroDivisionError:
                self.pixel[ind] = 0
        #self.pixel = [
        #    float(self.mrcHeader[10]) / self.mrcHeader[0],
        #    float(self.mrcHeader[11]) / self.mrcHeader[1],
        #    float(self.mrcHeader[12]) / self.mrcHeader[2]]
        self.length = [self.mrcHeader[10], self.mrcHeader[11], 
                       self.mrcHeader[12]]

        # read extended header if present
        self.extendedHeaderLength = self.mrcHeader[23]
        if header is None:
            self.extendedHeaderString = self.file_.read(
                self.extendedHeaderLength)
       
        return

    def writeMRC(self, file=None, header=None, byteOrder=None, shape=None,
                 dataType=None, arrayOrder=None, length=None, pixel=None,
                 data=None, extended=None, casting='unsafe'):
        """
        Writes MRC file (header and data).

        Values of all non-None arguments are saved as properties with same 
        names.

        Data (image) has to be specified by arg data or previously set 
        self.data attribute.

        Data type and shape are determined by args dataType and shape, 
        previously set attributes self.dataType and self.shape, or by the data 
        type and shape of the data, in this order.

        If data type (determined as described above) is not one of the mrc
        data types (ubyte, int16, float32, complex64), then the value of arg 
        dataType has to be one of the mrc data types. Otherwise an exception 
        is raised.

        If data type (determined as described above) is different from the 
        type of actual data, the data is converted to the data type. Note that
        if these two types are incompatible according to arg casting an 
        exception is raised. 

        Values for byteOrder and arrayOrder are set to the first value found 
        from the arguments, properties with same names, from mrcHeader of 
        default values. 
 
        Header parameters nxstart, nystart and nzstart are set to 0, while mx,
        my and mz to the corresponding data size (grid size). 

        MRC parameters xlen, ylen and zlen are taken from arg length if given,
        or obtained by multiplying data size with pixel size (in nm).

        MRC parameters min, max and mean are recalculated.

        All other header values are defined in the mrcDefaultHeader.
        The default value of axisOrder can be changed by setting 
        self.axisOrder.

        If data is not given, only a header is writen.
        """

        # open the file if needed
        self.checkFile(file_=file, mode='w')

        # set attributes from header
        if header is not None:
            self.parseMRCHeader(header=header)
        
        # buteOrder: use the argument, self.byteOrder, or the default value
        if byteOrder is not None: self.byteOrder = byteOrder
        if self.byteOrder is None:
            self.byteOrder = ImageIO.mrc['defaultByteOrder']

        # arrayOrder: use the argument, self.arrayOrder, or the default value
        if arrayOrder is not None: self.arrayOrder = arrayOrder
        if self.arrayOrder is None:
            self.arrayOrder = ImageIO.mrc['defaultArrayOrder']

        # data: use the argument or the self.data
        # sets self.data, self.shape and self.dataType
        if data is not None:
            self.setData(data, shape=shape)  
        
        # dataType: use the argument, self.dataType, or the mrcHeader value
        if dataType is not None: 
            self.dataType = dataType
        if self.dataType is None:
            if self.mrcHeader is not None:
                self.dataType = ImageIO.mrcDataTypeTab[self.mrcHeader[3]]

        # unit8 and ubyte are the same
        if self.dataType == 'uint8':
            self.dataType = 'ubyte'

        # convert data to another dtype if needed
        wrong_data_type = False
        try:
            if (self.dataType == 'ubyte') or (self.dataType == 'uint8'):
                if self.data.dtype.name != 'uint8':
                    self.data = self.data.astype(dtype='uint8', casting=casting)
            elif self.dataType == 'int16':
                if self.data.dtype.name != 'int16':
                    self.data = self.data.astype(dtype='int16', casting=casting)
            elif self.dataType == 'float32':
                if self.data.dtype.name != 'float32':
                    self.data = self.data.astype(dtype='float32', 
                                                 casting=casting)
            elif self.dataType == 'complex64':
                if self.data.dtype.name != 'complex64':
                    self.data = self.data.astype(dtype='complex64', 
                                                 casting=casting)
            else:
                wrong_data_type = True
        except TypeError:
            print("Error most likely because trying to cast " +  
                  self.data.dtype.name + " array to " + self.dataType +
                  " type. This may cause errors, so change argument dataType "
                  "to an appropriate one.")
            raise
        if wrong_data_type:
            raise TypeError(
                "Data type " + self.dataType + " is not valid for MRC"
                " format. Allowed types are: " 
                + str(ImageIO.mrcDataTypeTab.values()))

        # axisOrder: self.axisOrder or default
        if self.axisOrder is None:
            self.axisOrder = ImageIO.mrc['defaultAxisOrder']
        
        # shape: use the argument, self.shape, get from header, or use default
        #if shape is not None: self.shape = shape
        if self.shape is None:
            self.shape = copy(ImageIO.mrcDefaultShape)
        # probably not needed (15.01.08)
        #if self.shape is None:
        #    if self.mrcHeader is not None:
        #        self.shape = self.mrcHeader[0:3]
        #    else:
        #        self.shape = ImageIO.mrcDefaultShape

        # pixel size: use the argument, self.pixel, or the default value
        if pixel is not None:
            self.pixel = pixel
        if self.pixel is None:
            self.pixel = copy(ImageIO.mrcDefaultPixel)
        try:
            if not isinstance(self.pixel, (list, tuple)):
                self.pixel = [pixel] * len(self.shape)
        except (AttributeError, LookupError):
            print "Need to specify shape of the data."
            raise

        # length: use the argument, self.length, or shape * pixel
        if length is not None: self.length = length
        if self.length is None:
            try:
                self.length = numpy.asarray(self.shape) \
                    * numpy.asarray(self.pixel)
            except (AttributeError, LookupError):
                print "Need to specify shape of the data."
                raise

        # use header, self.mrcHeader or the default mrc header 
        if header is not None: 
            self.mrcHeader = header
        if self.mrcHeader is None: 
            self.mrcHeader = copy(ImageIO.mrcDefaultHeader)
        if extended is not None:
            self.extended = extended
        
        # add shape, data type and axisOrder to the header
        try:
            for k in range( len(self.shape) ): 
                self.mrcHeader[k] = self.shape[k]
                self.mrcHeader[k+7] = self.shape[k]
                self.mrcHeader[k+10] = self.length[k]
            try:
                self.mrcHeader[3] = ImageIO.mrcDataTypeTabInv[self.dataType]
            except KeyError:
                print("Data type " + self.dataType + " is not valid for MRC"
                      " format. Allowed types are: " 
                      + str(ImageIO.mrcDataTypeTab.values()))
                raise
            self.mrcHeader[16:19] = self.axisOrder
        except (AttributeError, LookupError):
            print "Need to specify data type and shape of the data."
            raise
 
        # add min max and mean values
        if self.data is not None:
            self.mrcHeader[19] = self.data.min()
            self.mrcHeader[20] = self.data.max()
            self.mrcHeader[21] = self.data.mean()
        
        # convert header to a string and write it
        self.headerString = struct.pack(ImageIO.mrc['headerFormat'],
                                        *tuple(self.mrcHeader))
        if extended is not None:
            self.headerString = self.headerString + extended
        self.file_.write(self.headerString)

        # write data if exist
        if self.data is not None: self.writeData()
        self.file_.flush()
        
        return


    #####################################################
    #
    # Raw file format
    #
    ######################################################

    # raw file format properties
    raw = { 'defaultHeaderSize': 0,
            'defaultByteOrder': machineByteOrder,
            'defaultArrayOrder': 'FORTRAN'
            }

    def readRaw(self, file=None, dataType=None, shape=None,
                byteOrder=None, arrayOrder=None, headerSize=None):
        """
        Reads raw data file.

        """
        
        # open the file if needed
        self.checkFile(file_=file, mode='r')

        # set defaults
        self.byteOrder = ImageIO.raw['defaultByteOrder']
        self.arrayOrder = ImageIO.raw['defaultArrayOrder']
 
        # parse arguments
        if file is not None: self.file_ = file
        if byteOrder is not None: self.byteOrder = byteOrder
        if dataType is not None: self.dataType = dataType
        if arrayOrder is not None: self.arrayOrder = arrayOrder
        if shape is not None: self.shape = shape
        if headerSize is not None: self.rawHeaderSize = headerSize

        # read header
        self.readRawHeader(file=self.file_, size=self.rawHeaderSize)

        # read data
        self.readData(shape=shape)

        return

    def readRawHeader(self, file=None, size=None):
        """
        Reads a header of a raw file.

        Sets:
          - headerString: header as a string 

        Arguments:
          - file: file name or a file instance
          - size: header size in bytes
        """

        # open the file if needed
        self.checkFile(file_=file, mode='r')

        # determine header size
        if size is not None:
            self.rawHeaderSize = size
        elif self.rawHeaderSize is None:
            self.rawHeaderSize = self.raw['defaultHeaderSize']

        # read the header
        if size > 0:
            self.headerString = self.file_.read(self.rawHeaderSize)
        else:
            self.headerString = ''

    def writeRaw(
        self, file=None, header=None, data=None, shape=None, 
        dataType=None, byteOrder=None, arrayOrder=None, casting='unsafe'):
        """
        Writes raw data.

        Values of all non-None arguments are saved as properties with same 
        names.

        Data (image) has to be specified by arg data or previously set 
        self.data attribute.

        Data type and shape are determined by args dataType and shape, 
        previously set attributes self.dataType and self.shape, or by the data 
        type and shape of the data, in this order.

        If data type (determined as described above) is different from the 
        type of actual data, the data is converted to the data type. Note that
        if these two types are incompatible an exception is raised. 

        Values for byteOrder and arrayOrder, are set to the first value found 
        from the arguments, or properties with same names. 
        """

        # open the file if needed
        self.checkFile(file_=file, mode='w')

        # set defaults
        self.arrayOrder = ImageIO.raw['defaultArrayOrder']
        self.byteOrder = ImageIO.raw['defaultByteOrder']
 
        # parse arguments
        if file is not None: self.file_ = file
        if data is not None:
            self.setData(data, shape=shape)    # sets self.shape also
        if byteOrder is not None: self.byteOrder = byteOrder
        if arrayOrder is not None: self.arrayOrder = arrayOrder

        # data type
        if dataType is not None: 
            self.dataType = dataType
        else:
            self.dataType = data.dtype.name
        if self.dataType != data.dtype.name:
            try:
                 self.data = self.data.astype(dtype=self.dataType, 
                                             casting=casting)
            except TypeError:
                print("Error most likely because trying to cast " +  
                      self.data.dtype.name + " array to " + self.dataType +
                      " type. This may cause errors, so change argument "
                      "dataType to an appropriate one.")
                raise
            
        # write header
        if header is not None:
            self.file_.write(header)

        # write data
        self.writeData()

        return


    ########################################################
    #
    # Common read/write methods
    #
    ########################################################

    def setData(self, data, shape=None):
        """
        Reshapes data according to the arg shape (if specified) and saves it
        to self.data, self.shape and self.dataType.
        """

        # make shape of length 3
        if (shape is not None) and (len(shape) < 3):
            if len(shape) == 2:
                shape = (shape[0], shape[1], 1)
            elif len(shape) == 1:
                shape = (shape[0], 1, 1)

        self.data = data
        if self.data is not None:
            if shape is not None:
                self.data = self.data.reshape(shape)
            self.shape = self.data.shape
            self.dataType = self.data.dtype.name
        
    def readData(self, shape=None):
        """
        Reads data from an image file to numpy.ndarray.

        Should not be used directly. Instance attributes: file, dataType,
        byteOrder, arrayOrder and shape have to be set before calling this 
        method.
        """

        # read data in numpy.ndarray 
        self.data = numpy.fromfile(file=self.file_, dtype=self.dataType)

        # reshape data
        if self.arrayOrder is None: 
            self.arrayOrder = self.defaultArrayOrder
        if shape is not None:
            self.shape = shape
        self.data = self.data.reshape(self.shape, order=self.arrayOrder)

        # chage byte order (to little-endian) if needed
        if self.byteOrder == '>': self.data = self.data.byteswap(True)

        return

    def writeData(self):
        """
        Writes data in numpy.ndarray format to an image file.

        Transforms self.data according to self.dataType, self.byteOrder and 
        self.shape before writing.

        Should not be used directly. Instance attributes: file, data, dataType,
        byteOrder, arrayOrder and shape have to be set before calling this 
        method.
        """

        # change dataType, byteOrder and arrayOrder if needed
        try:
            if self.data.dtype != self.dataType:
                self.data= numpy.asarray(self.data, dtype=self.dataType)
            if self.byteOrder == '>': 
                self.data = self.data.byteswap(True)
            self.data = self.data.reshape(self.data.size, 
                                          order=self.arrayOrder )
        except (AttributeError, LookupError):
            print "Need to specify data."
            raise

        # write
        self.data.tofile(file=self.file_)

        # reshape data back to original shape
        self.data = self.data.reshape(self.shape, order=self.arrayOrder)

    def setFileFormat(self, fileFormat=None, file_=None):
        """
        Sets self.fileFormat. 

        It is determined in the following order: first
        from the argument fileFormat, then from the file extension and
        finally from the already existing value of self.fileFormat

        Arguments:
          - file_: file name
          - fileFormat: file Format
        """
        
        if fileFormat is not None:

            # fileFormat argiment given
            self.fileFormat = fileFormat 

        else:

            # parse file_ argument
            if file_ is None:
                file_ = self.fileName

            # find the extension of file_ to determine the format
            if isinstance(file_, str):   # file argument is a file name 
                splitFileName = os.path.splitext(file_)
                extension = splitFileName[-1].lstrip('.')
                self.fileFormat = ImageIO.fileFormats.get(extension)
            else:
                # fileFormat not set here, raise an exception later if needed 
                pass
        
        return
    
    def checkFile(self, file_, mode):
        """
        If file_ is a string open the file with that name. If file_ is None,
        use self.fileName.

        If file_ is a file instance don't do anything.

        Sets:
          - self.fileName: file_ if a string
          - self.file_: file instance

        Arguments:
          - file_: file name or instance of file
          - mode: mode as in open()
        """

        # use self.fileName if file_ is None
        if file_ is None:
            file_ = self.fileName

        # open the file if not opened already
        if isinstance(file_, str):  # file_ is a string
            self.fileName = file_
            self.file_ = open(file_, mode)  

        elif isinstance(file_, file):  # file already open
            self.file_ = file_  

        else:
            raise IOError("Argument file_: " + str(file_)
                          + "is neither a string nor a file object")

        return


    ########################################################
    #
    # Header manipulations
    #
    ########################################################

    def getTiltAngle(self):
        """
        Returns titl angle in degrees.
        """

        # ToDo: get from header directly?
        if self.fileFormat == 'em':
            return self._tiltAngle / 1000.

        else:
            raise ValueError("Sorry can't get tilt angle for " +
                                      self.fileFormat + " file.")

    def setTiltAngle(self, angle):
        """
        Sets self._tiltAngle to angle*1000 and puts that value in emHeader.

        Works only for em format.
        """
        if self.fileFormat == 'em':

            # set the attribute
            self._tiltAngle = angle * 1000

            # put in the emHeader
            self.putInEMHeader(name='_tiltAngle', value=self._tiltAngle)

        else:
            raise ValueError("Sorry, can't get tilt angle for " +
                                      self.fileFormat + " file.")

    tiltAngle = property(fget=getTiltAngle, fset=setTiltAngle,
                         doc='Tilt angle (in deg)')

    def getPixelsize(self):
        """
        Returns pixel size (at specimen level) in nm.

        For mrc files a single pixelsize is returned if it's the same for all 
        dimensions, otherwise a list of pixelsizes (for each dimension) is
        returned.
        """
        if self.fileFormat == 'em':
            return self._pixelsize / 1000.
        elif self.fileFormat == 'mrc':
            if isinstance(self.pixel, (int, float)):
                return self.pixel
            else:
                if (numpy.asarray(self.pixel) == self.pixel[0]).all():
                    return self.pixel[0]
                else:
                    return self.pixel
        else:
            raise ValueError("Sorry can't get pixel size for " +
                                      self.fileFormat + " file.")

    pixelsize = property(fget=getPixelsize, 
                         doc="Pixel size (at specimen level) in nm")

    def fix(self, mode=None, microscope=None):
        """
        Fixes wrong values in header and in the data. 
        
        Mode determines which values are fixed. Currently defined modes are:
          - 'polara_fei-tomo': images obtained on Polara (at MPI of 
          Biochemistry) using FEI tomography package and saved in EM 
          format.
          - 'krios_fei-tomo': images obtained on Krios (at MPI of 
          Biochemistry) using FEI tomography package and saved in EM 
          format.
          - 'cm300': images from cm300 in EM format

        If mode is polara_fei-tomo, then arg microscope has to be specified. 
        The allowed values are specified in microscope_db.py. Currently (r564) 
        these are: 'polara-1_01-07', 'polara-1_01-09' and 'polara-2_01-09'.

        """

        self.fixHeader(mode=mode, microscope=microscope)

        # fix data to be implemented

    def fixHeader(self, mode=None, microscope=None):
        """
        Fixes wrong values in microscope image header.

        Mode determines which values are fixed. Currently defined modes are:
          - 'polara_fei-tomo': images obtained on Polara (at MPI of 
          Biochemistry) using FEI tomography package and saved in EM 
          format. Values fixed:
            - voltage: set to 300000
            - cs: set to 2000
            - ccdPixelsize: physical pixel size, read from microscope_db
            - ccdLength: physical size of the CCD, pixelsize x n_pixels
            - _pixelsize: pixel size at the specimen level [fm]. Nominal mag
            is read from the header and converted to pixelsize using
            microscope_db
          - 'krios_fei-tomo': images obtained on Krios (at MPI of 
          Biochemistry) using FEI tomography package and saved in EM 
          format. Pixel size at the specimen level is correct, and the physical 
          detector length might be correct. Values fixed:
            - voltage: set to 300000
            - cs: set to 2000
          - 'cm300': images from cm300 in EM format
          - None: doesn't do anything

        If mode is 'polara_fei-tomo', then arg microscope has to be specified. 
        The allowed values are specified in microscope_db.py. Currently (r564)
        these are: 'polara-1_01-07', 'polara-1_01-09' and 'polara-2_01-09'.

        Updates the appropriate header: self.emHeader if file format is 'em',
        or self.mrcHeader for mrc files.
        """

        if self.fileFormat == 'em':

            if mode == 'polara_fei-tomo':

                # put voltage
                self.putInEMHeader(name='voltage', value=300000)
                
                # put cs
                self.putInEMHeader(name='cs', value=2000)

                # put CCD pixel size
                ccd_pixelsize = microscope_db.ccd_pixelsize[microscope]
                self.putInEMHeader(name='ccdPixelsize', value=ccd_pixelsize)

                # put CCD length (pixel size * number of pixels)
                self.putInEMHeader(name='ccdLength',
                                   value=microscope_db.n_pixels[microscope] \
                                       * ccd_pixelsize)

                # get nominal magnification and determine (real) pixel size
                mag = self.getFromEMHeader('magnification')
                pixelsize = microscope_db.pixelsize[microscope][mag]
                self.putInEMHeader(name='_pixelsize', value=pixelsize)

            elif mode == 'krios_fei-tomo':

                # put voltage
                self.putInEMHeader(name='voltage', value=300000)
                
                # put cs
                self.putInEMHeader(name='cs', value=2000)

                # put CCD pixel size
                #ccd_pixelsize = microscope_db.ccd_pixelsize[microscope]
                #self.putInEMHeader(name='ccdPixelsize', value=ccd_pixelsize)

                # put CCD length (pixel size * number of pixels)
                # The value might be correct
                #self.putInEMHeader(
                #    name='ccdLength',
                #    value=microscope_db.n_pixels[microscope] * ccd_pixelsize)

                # get nominal magnification and determine (real) pixel size
                # not needed because correct value there already
                #mag = self.getFromEMHeader('magnification')
                #pixelsize = microscope_db.pixelsize[microscope][mag]
                #self.putInEMHeader(name='_pixelsize', value=pixelsize)

            elif mode == 'cm300':
                microscope = 'cm300'

                # put voltage
                self.putInEMHeader(name='voltage', value=300000)
                
                # put cs
                self.putInEMHeader(name='cs', value=2000)

                # get magnification and determine (real) pixel size
                mag = self.getFromEMHeader('magnification')
                nom_mag = microscope_db.nominal_mag[microscope][mag]
                pixelsize = microscope_db.pixelsize[microscope][nom_mag]
                self.putInEMHeader(name='_pixelsize', value=pixelsize) 

                # correct em code
                self.putInEMHeader(name='emCode', value=0)

                # put CCD pixel size
                ccd_pixelsize = microscope_db.ccd_pixelsize[microscope]
                self.putInEMHeader(name='ccdPixelsize', value=ccd_pixelsize)

                # put CCD length (pixel size * number of pixels)
                self.putInEMHeader(name='ccdLength',
                                   value=microscope_db.n_pixels[microscope] * \
                                       ccd_pixelsize)

            elif mode is None:
                pass

            else:
                raise ValueError("Sorry, mode: " + str(mode) + 
                     " is not recognized for an " + self.fileFormat + " file.")
        
        elif self.fileFormat == 'mrc':
            
            if mode is None:
                pass

            else:
                raise ValueError("Sorry, mode: " + mode + 
                     " is not recognized for an " + self.fileFormat + " file.")

        elif self.fileFormat == 'raw':
            
            if mode is None:
                pass

            else:
                raise ValueError("Sorry, mode: " + mode + 
                     " is not recognized for an " + self.fileFormat + " file.")

        else:
            raise ValueError("Sorry, file format: " + self.fileFormat 
                                      + " is not recognized.") 
                

    def getFromEMHeader(self, name):
        """
        Reads the value of variable name from self.emHeader and returns it.

        Comment: alternatively, self.name can be used. Not sure which
        approach is better (VL 04.01.01).
        """

        # find position of name in self.emHeaderFields
        ind = 0
        reg = re.compile(name + '\\b')
        for field in self.emHeaderFields:
            if reg.match(field)is not None: break
            ind +=1

        # return the value
        return self.emHeader[ind]

    def putInEMHeader(self, name, value):
        """
        Puts value in self.EmHeaderFields at the position corresponding to
        name.
        """

        # find position of name in self.emHeaderFields
        ind = 0
        reg = re.compile(name + '\\b')
        for field in self.emHeaderFields:
            if reg.match(field)is not None: break
            ind +=1

        # put the value in 
        self.emHeader[ind] = value
        
