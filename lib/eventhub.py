from hashlib.sha256 import sha256
import base64
import hmac
import urlencode
import ntptime
import time


class EventHub():

    def __init__(self, hubAddress, eventHubName, eventHubPolicyName, sharedAccessKey):
        self.sharedAccessKey = sharedAccessKey
        self.EVENT_HUB_END_POINT = "/%s/publishers/%s/messages"
        self.eventHubPolicyName = eventHubPolicyName
        self.eventHubName = eventHubName
        self.hubAddress = hubAddress

        self.endpoint = self.EVENT_HUB_END_POINT % (
            self.eventHubName, self.eventHubPolicyName)
        self.sasUrl = "https://" + self.hubAddress + self.endpoint

    # sas generator from https://github.com/bechynsky/AzureIoTDeviceClientPY/blob/master/DeviceClient.py
    def generate_sas_token(self, expiry=3600):  # default to one hour expiry period
        urlencoder = urlencode.Urlencode()

        # Time Epoch: Unix port uses standard for POSIX systems epoch of 1970-01-01 00:00:00 UTC.
        # However, embedded ports use epoch of 2000-01-01 00:00:00 UTC.
        # 946684800 is the offset from embedded epoch and unix epoch bases

        now = 0

        while now == 0:
            try:
                now = ntptime.time() + 946684800
            except:
                time.sleep(1)

        ttl = now + expiry
        urlToSign = urlencoder.quote(self.sasUrl)

        msg = "{0}\n{1}".format(urlToSign, ttl).encode('utf-8')

        h = hmac.HMAC(bytearray(self.sharedAccessKey),
                      msg=msg, digestmod=sha256)
        decodedDigest = base64.b64encode(h.digest()).decode()
        signature = urlencoder.quote(decodedDigest)
        sas = "SharedAccessSignature sr={0}&sig={1}&se={2}&skn={3}".format(
            urlToSign, signature, ttl, self.eventHubPolicyName)
        # print(sas)
        return sas
