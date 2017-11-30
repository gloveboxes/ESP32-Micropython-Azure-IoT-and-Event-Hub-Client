from hashlib.sha256 import sha256
import base64
import hmac
import urlencode
import ntptime


class IotHub():

    def __init__(self, hubAddress, deviceId, sharedAccessKey):
        self.sharedAccessKey = sharedAccessKey
        self.endpoint = hubAddress + '/devices/' + deviceId
        self.hubUser = hubAddress + '/' + deviceId
        self.hubTopicPublish = 'devices/' + deviceId + '/messages/events/'
        self.hubTopicSubscribe = 'devices/' + deviceId + '/messages/devicebound/#'
        
    # sas generator from https://github.com/bechynsky/AzureIoTDeviceClientPY/blob/master/DeviceClient.py
    def generate_sas_token(self, expiry=3600): # default to one hour expiry period
        urlencoder = urlencode.Urlencode()

        # Time Epoch: Unix port uses standard for POSIX systems epoch of 1970-01-01 00:00:00 UTC. 
        # However, embedded ports use epoch of 2000-01-01 00:00:00 UTC.
        # 946684800 is the offset from embedded epoch and unix epoch bases
        retry = True
        now = 0

        while retry:
          try:
            now = ntptime.time() + 946684800
            retry = False
          except:
            retry = True

        ttl = now + expiry        
        urlToSign = urlencoder.quote(self.endpoint)         
        sign_sharedAccessKey = "%s\n%d" % (urlToSign, int(ttl))
        msg = "{0}\n{1}".format(urlToSign, ttl).encode('utf-8')
        key = base64.b64decode(self.sharedAccessKey)
        h = hmac.HMAC(key, msg = msg, digestmod=sha256)
        decodedDigest = base64.b64encode(h.digest()).decode()
        signature = urlencoder.quote(decodedDigest)
        sas = "SharedAccessSignature sr={0}&sig={1}&se={2}".format(urlToSign, signature, ttl)
        # print(sas)
        return sas