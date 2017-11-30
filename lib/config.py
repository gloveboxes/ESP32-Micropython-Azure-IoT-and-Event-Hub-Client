import ujson as json

class Config():

    def config_load(self, configFile):
        #global sensor, hubAddress, deviceId, sharedAccessKey, owmApiKey, owmLocation
        try:
            print('Loading {0} settings'.format(configFile))

            config_data = open(configFile)
            config = json.load(config_data)

            self.sensor = __import__(config['SensorModule'])
            self.host = config['Host']
            self.key = config['Key']
            self.deviceId = config['DeviceId']
            self.sampleRate = config['SampleRate']            
            self.wifiSsid = config['WifiSsid']
            self.wifiPwd = config['WifiPwd']
            self.location = config['Location']


        except:
            print('Error loading config data')

    def __init__(self, configFile):
        self.config_load(configFile)