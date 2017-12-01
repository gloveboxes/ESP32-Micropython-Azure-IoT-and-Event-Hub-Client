import iothub
import socket
import ussl
import utime as time
import network
from machine import I2C, Pin, ADC
import ssd1306 as oled
import gc
import config

i2c = I2C(scl=Pin(4), sda=Pin(5))
builtinLedPin = 5

display = None
builtinLed = None

cfg = config.Config('config.json')
mySensor = cfg.sensor.Sensor(i2c)
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
    global display, builtinLed
    i2cDevices = I2C.scan(i2c)
    if 60 in i2cDevices:
        display = oled.SSD1306_I2C(128, 64, i2c)
        return True
    else:
        builtinLed = Pin(builtinLedPin, Pin.OUT)
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
        if not oledDisplay:
            builtinLed.value(0)  # turn on led

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

        data = b'{"DeviceId":"%s","Id":%u,"Mem":%u,"Celsius":%s,"hPa":%s,"Humidity":%s, "Geo":"%s", "Light":%d, "Errors":%d}' % (
            cfg.deviceId, count, freeMemory, temperature, pressure, humidity, cfg.location, light, errorCount)

        try:
            s = socket.socket()
            s.connect(addr)
            s = ussl.wrap_socket(s)  # SSL wrap

            # Send POST request to Azure IoT Hub
            s.write("POST /devices/" + cfg.deviceId +
                    "/messages/events?api-version=2016-02-03 HTTP/1.0\r\n")
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
            if not oledDisplay:
                builtinLed.value(1)  # turn off led

            print('messages sent: %d, errors: %d' % (count, errorCount))
            time.sleep(cfg.sampleRate)


oledDisplay = initDisplay(i2c)
if oledDisplay:
    display.text("welcome", 0, 0)
    display.show()

wlan_connect(cfg.wifiSsid, cfg.wifiPwd)

time.sleep(2)  # allow for a little settle time
main()
