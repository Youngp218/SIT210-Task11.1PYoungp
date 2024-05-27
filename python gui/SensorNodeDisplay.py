from PyQt5 import QtWidgets, QtCore
import requests

class SensorNodeDisplay(QtWidgets.QWidget):
    updateComplete = QtCore.pyqtSignal()
    
    def __init__(self, thingspeak_channel: str, thingspeak_key: str, initialValues: list):
        super().__init__()
        self.api_endpoint = "https://api.thingspeak.com/channels/" + thingspeak_channel + "/feeds/last.json?api_key=" + thingspeak_key
        self.luxValue = initialValues[0]
        self.soilValue = initialValues[1]
        self.tempValue = initialValues[2]
        self.soundValue = initialValues[3]
        self.initUI()
        
    def initUI(self):
        self.grid = QtWidgets.QGridLayout(self)
        self.initLuxGroup() # UV/light level on the sensor node
        self.initSoilMoistureGroup() # soil readings
        self.initTempGroup() #temperature 
        self.initSoundGroup() #ambient sound (e.g. thunderstorms)
    
    def initLuxGroup(self):
        # For prototyping reasons this is measuring light level, however ideally it would be a UV reading
        self.luxGroup  = QtWidgets.QGroupBox("UV Readings", self)
        self.luxLabel  = QtWidgets.QLabel(self.updateLuxLabel(self.luxValue), self)
        self.luxBlurb  = self.generateLabel("A UV rating of 1-2 is low, while 10+ is extreme and can damage skin or cause cancer.")
        self.vLuxBox = QtWidgets.QVBoxLayout(self.luxGroup)
        self.vLuxBox.addWidget(self.luxBlurb, 0)
        self.vLuxBox.addWidget(self.luxLabel, 1)
        self.grid.addWidget(self.luxGroup, 0,0)
    
    def initSoilMoistureGroup(self):
        self.soilGroup  = QtWidgets.QGroupBox("Soil Readings", self)
        self.soilLabel  = QtWidgets.QLabel(self.updateSoilLabel(self.soilValue), self)
        self.soilBlurb  = self.generateLabel("A soil moisture rating of 20% is considered dry, and 80% is considered extremely moist.")
        self.vSoilBox = QtWidgets.QVBoxLayout(self.soilGroup)
        self.vSoilBox.addWidget(self.soilBlurb, 0)
        self.vSoilBox.addWidget(self.soilLabel, 1)
        self.grid.addWidget(self.soilGroup, 0,1)
    
    def initTempGroup(self):
        self.tempGroup  = QtWidgets.QGroupBox("Temp Readings", self)
        self.tempLabel  = QtWidgets.QLabel(self.updateTempLabel(self.tempValue), self)
        self.tempBlurb  = self.generateLabel("A temperature of 0 degrees Celsius freezes water, and 40 degrees Celsius can quickly cause heatstroke.")
        self.vTempBox = QtWidgets.QVBoxLayout(self.tempGroup)
        self.vTempBox.addWidget(self.tempBlurb, 0)
        self.vTempBox.addWidget(self.tempLabel, 1)
        self.grid.addWidget(self.tempGroup, 1,0)
    
    def initSoundGroup(self):
        # For prototyping reasons this is measuring analogue sound level, however ideally it would be a true decibel reading
        self.soundGroup  = QtWidgets.QGroupBox("Sound Readings", self)
        self.soundLabel  = QtWidgets.QLabel(self.updateSoundLabel(self.soundValue), self)
        self.soundBlurb  = self.generateLabel("A sound rating of 85 dBA is enough to cause hearing damage with repeated exposure.")
        self.vSoundBox = QtWidgets.QVBoxLayout(self.soundGroup)
        self.vSoundBox.addWidget(self.soundBlurb, 0)
        self.vSoundBox.addWidget(self.soundLabel, 1)
        self.grid.addWidget(self.soundGroup, 1,1)
    
    #Populates values from thingspeak API response
    def updateLabels(self, response):
        # if there hasn't been any data pushed to the channel, or another error
        if response == -1:
            return
        self.luxValue = float(response["field1"])
        self.luxLabel.setText(self.updateLuxLabel(self.luxValue))
        self.soilValue = float(response["field2"])
        self.soilLabel.setText(self.updateSoilLabel(self.soilValue))
        self.tempValue = float(response["field3"])
        self.tempLabel.setText(self.updateTempLabel(self.tempValue))
        self.soundValue = float(response["field4"])
        self.soundLabel.setText(self.updateSoundLabel(self.soundValue))
        self.update()
        
    # Helper functions to keep the code D.R.Y.
    def generateLabel(self, title):
        newLabel = QtWidgets.QLabel(title, self)
        newLabel.setWordWrap(True)
        return newLabel
    
    def updateLuxLabel(self, val):
        return "Current light level: %.2f lux" % val
        
    def updateSoilLabel(self, val):
        return "Current soil moisture: %.2f%%" % val
    
    def updateTempLabel(self, val):
        return "Current temperature: %.2f Celsius" % val
    
    def updateSoundLabel(self, val):
        return "Current loudness: %.2f dBA" % val

class NodeUpdateWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(object)
    def __init__(self, api_endpoint: str):
        super().__init__()
        self.api_endpoint = api_endpoint
        
    def getValues(self):
        try:
            response = requests.get(self.api_endpoint).json()
        except:
            response = -1
        self.finished.emit(response)