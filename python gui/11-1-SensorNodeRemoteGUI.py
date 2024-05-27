from PyQt5 import QtWidgets, QtCore
import sys
import SensorNodeDisplay
import SECRETS

# Strongly type the list of nodes, so it always knows what it's working with
type NodeList = list[SensorNodeDisplay.SensorNodeDisplay]
type ThreadList = list[QtCore.QThread]
type WorkerList = list[SensorNodeDisplay.NodeUpdateWorker]

class NodeSelectorWindow(QtWidgets.QMainWindow):
    def __init__(self, app: QtWidgets.QApplication):
        super(NodeSelectorWindow, self).__init__()
        self.app = app
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.initUI()
        self.thingspeakTimer = QtCore.QTimer(self)
        
    def initUI(self):
        self.tabs = QtWidgets.QTabWidget(self)
        self.nodes: NodeList = []
        self.vMainBox = QtWidgets.QVBoxLayout(self.main_widget)
        self.quitApp = QtWidgets.QPushButton("Exit", self)
        self.quitApp.clicked.connect(self.exitOnClick)
        self.vMainBox.addWidget(self.tabs)
        self.vMainBox.addWidget(self.quitApp)
    
    def updateScenes(self):
        self.progress = 0
        self.nodeLength = len(self.nodes)
        self.threads: ThreadList = []
        self.workers: WorkerList = []
        if self.nodeLength == 0:
            self.restartTimer()
            return
        for node in self.nodes:
            self.threads.append(QtCore.QThread())
            self.workers.append(SensorNodeDisplay.NodeUpdateWorker(node.api_endpoint))
            self.workers[-1].moveToThread(self.threads[-1])
            self.threads[-1].started.connect(self.workers[-1].getValues)
            self.workers[-1].finished.connect(self.threads[-1].quit)
            self.workers[-1].finished.connect(node.updateLabels)
            self.workers[-1].finished.connect(self.workers[-1].deleteLater)
            self.workers[-1].finished.connect(self.restartTimer)
            self.threads[-1].finished.connect(self.threads[-1].deleteLater)
            self.threads[-1].start()
        
    #QTimer also has a regular repeating timer option, however if there's any issue 
    #with the network request (need to re-establish connection, slow speed, etc)
    #it runs the risk of firing twice concurrently, so instead the timer is restarted 
    #after the code is executed
    def restartTimer(self):
        self.progress += 1
        if (self.progress >= self.nodeLength):
            self.nodeLength = 0
            self.thingspeakTimer.singleShot(5000, self.updateScenes)
    
    def exitOnClick(self):
        self.app.quit()
    
    def addNode(self, channel: str, key: str, name: str, initialValues=[-1,-1,-1,-1]):
        self.nodes.append(SensorNodeDisplay.SensorNodeDisplay(
            thingspeak_channel=channel, 
            thingspeak_key=key, 
            initialValues=initialValues))
        self.tabs.addTab(self.nodes[-1], name)
        #if this is the first node added, start the regular update timer
        if len(self.nodes) == 1: self.updateScenes()


def window():
    app = QtWidgets.QApplication(sys.argv)
    win = NodeSelectorWindow(app)
    win.addNode(SECRETS.THINGSPEAK_CHANNEL_ID, SECRETS.THINGSPEAK_READ_API_KEY, "Backyard Node", [13, 200, 40, 16])
    #Dummy node that has no corresponding channel on thingspeak
    win.addNode("SECRETS.THINGSPEAK_CHANNEL_ID", "SECRETS.THINGSPEAK_READ_API_KEY", "Uninitialized Node")
    win.setGeometry(400, 400, 600, 300)
    win.setWindowTitle("Task 10.1 BoM Node Inspector")
    win.show()
    sys.exit(app.exec_())

window()
        