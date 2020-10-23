import PyIndi
from astropy.table import Table
from astroquery.astrometry_net import AstrometryNet
import photutils
import time
import sys
import threading
import os
     
class IndiClient(PyIndi.BaseClient):
    def __init__(self):
        super(IndiClient, self).__init__()
    def newDevice(self, d):
        pass
    def newProperty(self, p):
        pass
    def removeProperty(self, p):
        pass
    def newBLOB(self, bp):
        global blobEvent
        print("new BLOB ", bp.name)
        blobEvent.set()
        pass
    def newSwitch(self, svp):
        pass
    def newNumber(self, nvp):
        pass
    def newText(self, tvp):
        pass
    def newLight(self, lvp):
        pass
    def newMessage(self, d, m):
        pass
    def serverConnected(self):
        pass
    def serverDisconnected(self, code):
        pass

# Set variables
debug=1
exposure=5.0
telescope="Telescope Simulator"
device_telescope=None
telescope_connect=None
ccd="CCD Simulator"
solveOk=0
ast = AstrometryNet()
ast.api_key = 'gymdcmjzgjwdnjra'
plateSolve = 0 # 0=astrometry.net 1=local 2=remote
 
# connect the server
indiclient=IndiClient()
indiclient.setServer("localhost",7624)
 
if (not(indiclient.connectServer())):
     print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
     print("  indiserver indi_simulator_telescope indi_simulator_ccd")
     sys.exit(1)
 
# get the telescope device
device_telescope=indiclient.getDevice(telescope)
while not(device_telescope):
    time.sleep(0.5)
    device_telescope=indiclient.getDevice(telescope)
     
# wait CONNECTION property be defined for telescope
telescope_connect=device_telescope.getSwitch("CONNECTION")
while not(telescope_connect):
    time.sleep(0.5)
    telescope_connect=device_telescope.getSwitch("CONNECTION")
 
# if the telescope device is not connected, we do connect it
if not(device_telescope.isConnected()):
    # Property vectors are mapped to iterable Python objects
    # Hence we can access each element of the vector using Python indexing
    # each element of the "CONNECTION" vector is a ISwitch
    telescope_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
    telescope_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
    indiclient.sendNewSwitch(telescope_connect) # send this new value to the device

# We want to set the ON_COORD_SET switch to engage tracking after goto
# device.getSwitch is a helper to retrieve a property vector
telescope_on_coord_set=device_telescope.getSwitch("ON_COORD_SET")
while not(telescope_on_coord_set):
    time.sleep(0.5)
    telescope_on_coord_set=device_telescope.getSwitch("ON_COORD_SET")

# the order below is defined in the property vector, look at the standard Properties page
# or enumerate them in the Python shell when you're developing your program
telescope_on_coord_set[0].s=PyIndi.ISS_ON  # TRACK
telescope_on_coord_set[1].s=PyIndi.ISS_OFF # SLEW
telescope_on_coord_set[2].s=PyIndi.ISS_OFF # SYNC
indiclient.sendNewSwitch(telescope_on_coord_set)

# Set up coordinates 
telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
while not(telescope_radec):
    time.sleep(0.5)
    telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")      

# Set up CCD camera 
device_ccd=indiclient.getDevice(ccd)
while not(device_ccd):
    time.sleep(0.5)
    device_ccd=indiclient.getDevice(ccd)   
 
ccd_connect=device_ccd.getSwitch("CONNECTION")
while not(ccd_connect):
    time.sleep(0.5)
    ccd_connect=device_ccd.getSwitch("CONNECTION")
if not(device_ccd.isConnected()):
    ccd_connect[0].s=PyIndi.ISS_ON  # the "CONNECT" switch
    ccd_connect[1].s=PyIndi.ISS_OFF # the "DISCONNECT" switch
    indiclient.sendNewSwitch(ccd_connect)
 
ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")
while not(ccd_exposure):
    time.sleep(0.5)
    ccd_exposure=device_ccd.getNumber("CCD_EXPOSURE")
 
# Ensure the CCD simulator snoops the telescope simulator
ccd_active_devices=device_ccd.getText("ACTIVE_DEVICES")
while not(ccd_active_devices):
    time.sleep(0.5)
    ccd_active_devices=device_ccd.getText("ACTIVE_DEVICES")
ccd_active_devices[0].text="Telescope Simulator"
indiclient.sendNewText(ccd_active_devices)
 
# we should inform the indi server that we want to receive the
# "CCD1" blob from this device
indiclient.setBLOBMode(PyIndi.B_ALSO, ccd, "CCD1")
ccd_ccd1=device_ccd.getBLOB("CCD1")
while not(ccd_ccd1):
    time.sleep(0.5)
    ccd_ccd1=device_ccd.getBLOB("CCD1")

###############################################################
## M A I N                                                   ##
###############################################################
while (1):        # Loop forever
    # Update coordinates 
    telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
    while not(telescope_radec):
        time.sleep(0.5)
        telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")      

    if (telescope_radec.s==PyIndi.IPS_BUSY):
        if (debug==1):
             print("Scope Moving ", telescope_radec[0].value, telescope_radec[1].value)
             time.sleep(2)  
    else:
        # Scope is not moving - are we finished or do we need another image?
        if (solveOk):
            continue
        # Initiate an image on the camera
        # we use here the threading.Event facility of Python
        # we define an event for newBlob event
        blobEvent=threading.Event()
        blobEvent.clear()
        ccd_exposure[0].value=exposure
        indiclient.sendNewNumber(ccd_exposure)
        blobEvent.wait()
        blobEvent.clear()
        #indiclient.sendNewNumber(ccd_exposure)
        print("name: ", ccd_ccd1[0].name," size: ", ccd_ccd1[0].size," format: ", ccd_ccd1[0].format)
        fits=ccd_ccd1[0].getblobdata()
        # Write the image to disk
        filehandle = open('solve.fits', 'wb')
        filehandle.write(fits)
        filehandle.close()

        # Do a plate solve on the fits data
        if (plateSolve == 0):
            try_again = True
            submission_id = None

            while try_again:
                try:
                    if not submission_id:
                        wcs_header = ast.solve_from_image('solve.fits',submission_id=submission_id)
                    else:
                        wcs_header = ast.monitor_submission(submission_id,solve_timeout=120)
                except TimeoutError as e:
                    submission_id = e.args[1]
                else:
                   # got a result, so terminate
                   try_again = False

        elif (plateSolve == 1): # Local solver
            cmd="solve-field -O --no-plots --no-verify --resort --downsample 2 -3 "+str(telescope_radec[0].value)+" -4 "+str(telescope_radec[1].value)+" -L 24.1478 -H 26.6897 -u aw -5 30 solve.fits &> solve.err"
            if (debug): 
                print("Solving...")
                print(cmd)
            os.system(cmd)
      
        if (wcs_header):
            print("Solve successful...")
            print(wcs_header)
        else:
            print("Error, solve unsuccessful")
        exit()     
        
          
        # Compare the plate solve to the current RA/DEC
        
        # If within the threshold arcsecs set solveOk and continue
 
        # Otherwise set the desired coordinate and slew
        #telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
        #while not(telescope_radec):
        #    time.sleep(0.5)
        #telescope_radec=device_telescope.getNumber("EQUATORIAL_EOD_COORD")
        #telescope_radec[0].value=vega['ra']
        #telescope_radec[1].value=vega['dec']
        #indiclient.sendNewNumber(telescope_radec)
        # and wait for the scope has finished moving
        #while (telescope_radec.s==PyIndi.IPS_BUSY):
        #   print("Scope Moving ", telescope_radec[0].value, telescope_radec[1].value)
        #   time.sleep(2)

