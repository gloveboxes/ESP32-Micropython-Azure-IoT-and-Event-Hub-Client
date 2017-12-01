# TCP support
# https://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/network_tcp.html

# DHT11 and DHT22 library
# https://docs.micropython.org/en/latest/esp8266/esp8266/tutorial/dht.html
# import dht
# functions related to the board - http://docs.micropython.org/en/latest/esp8266/library/machine.html

import iothub
import socket
# SSL wrapper for Socket
import ussl
import utime as time
import network
from machine import I2C, Pin, ADC
import ssd1306 as oled
import fake_sensor
import gc
import config

# Azure IoT Hub configuration
# https://docs.microsoft.com/en-us/azure/iot-hub/
# Shared Access Signature
# SAS = "SharedAccessSignature sr=IoTCampAU.azure-devices.net%2Fdevices%2Fesp32&sig=y5NOb%2FhUnm%2FQbzWRZaZIYID7Rp7NvyI%2FK%2FGRPPUP%2FLM%3D&se=1511942058"
# Host name
# HOST = "IoTCampAU.azure-devices.net"
# # Device name
# DEVICE = "esp32"

# KEY = "w64FgOARiFIKBcy2WpLcjkkNGVDCcEw+h0QVeclKSrY="
# SSID = "NCW"
# WIFIPASSWORD = "malolos5459"

i2c = I2C(scl=Pin(4), sda=Pin(5))
display = None

builtinLedPin = 5
builtinLed = Pin(builtinLedPin, Pin.OUT)

cfg = config.Config('config.json')

mySensor = cfg.sensor.Sensor()
# mySensor = fake_sensor.Sensor()

iot = iothub.IotHub(cfg.host, cfg.deviceId, cfg.key)

wlan = network.WLAN(network.STA_IF)

lastUpdated = 0
updateSas = True

def newSasToken():
  global lastUpdated, updateSas, SAS
  if time.ticks_diff(time.time(), lastUpdated) > 60 * 15:
    lastUpdated = time.time()
    updateSas = True

  if updateSas:
    SAS = iot.generate_sas_token()
    print('Updating Sas')
    updateSas = False

def initDisplay(i2c):
    global display
    i2cDevices = I2C.scan(i2c)
    if 60 in i2cDevices:
        display = oled.SSD1306_I2C(128, 64, i2c)
        return True
    else:
        print('No OLED Display found')
        return False

def wlan_connect(ssid='MYSSID', password='MYPASS'):
    if not wlan.active() or not wlan.isconnected():
        wlan.active(True)
        print('connecting to:', ssid)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


def checkwifi():
    blinkcnt = 0
    while not wlan.isconnected():
        time.sleep_ms(500)


def main(use_stream=True):

    s = socket.socket()
    ai = socket.getaddrinfo(cfg.host, 443)
    addr = ai[0][-1]
    s.close()

    count = 0
    errorCount = 0

    while True:
      builtinLed.value(0) # turn on led
      checkwifi()
      newSasToken()
      count = count + 1  

      temperature, pressure, humidity = mySensor.measure()
      light = 0
      freeMemory = gc.mem_free()

      if oledDisplay:
        display.fill(0)
        display.text('t:' + str(temperature), 0, 0)
        display.text('p:' + str(pressure), 0, 9)
        display.text('h:' + str(humidity), 0, 18)
        display.text('m:' + str(freeMemory), 0, 27)
        display.text('c:' + str(count), 0, 36)
        display.text('d:' + cfg.deviceId, 0, 45)
        display.text('e:' + str(errorCount), 0, 53)
        display.show()

      data = b'{"DeviceId":"%s","Id":%u,"Mem":%u,"Celsius":%s,"hPa":%s,"Humidity":%s, "Geo":"%s", "Light":%d, "Errors":%d}' % (cfg.deviceId, count, freeMemory, temperature, pressure, humidity, cfg.location, light, errorCount)

      try:
        s = socket.socket()
        s.connect(addr)        
        s = ussl.wrap_socket(s) # SSL wrap
        
        # Send POST request to Azure IoT Hub
        s.write("POST /devices/" + cfg.deviceId + "/messages/events?api-version=2016-02-03 HTTP/1.0\r\n")
        # HTTP Headers
        s.write("Host: " + cfg.host + "\r\n")
        s.write("Authorization: " + SAS + "\r\n")
        s.write("Content-Type: application/json\r\n")
        s.write("Connection: close\r\n")
        s.write("Content-Length: " + str(len(data)) + "\r\n\r\n")
        # Data
        s.write(data)
        
        # Print 128 bytes of response
        print(s.read(128)[:12])

        s.close()
      except:
        print('Problem posting data')
        errorCount = errorCount + 1
      finally:
        builtinLed.value(1) # turn off led
        print('messages sent: %d, errors: %d' % (count, errorCount))
        time.sleep(cfg.sampleRate)
        



oledDisplay = initDisplay(i2c)
if oledDisplay:
  display.text("welcome", 0, 0)
  display.show()

wlan_connect(cfg.wifiSsid, cfg.wifiPwd)

time.sleep(2)
# SAS = iot.generate_sas_token()


# Run

main()