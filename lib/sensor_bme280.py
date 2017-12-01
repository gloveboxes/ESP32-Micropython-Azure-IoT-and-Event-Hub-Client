import bme280


class Sensor():

    def __init__(self, i2c_config):
        self.bme = bme280.BME280(i2c=i2c_config)

    def measure(self):
        v = self.bme.values

        temperature = v[0][:-1]
        pressure = v[1][:-3]
        humidity = v[2][:-1]

        return (temperature, pressure, humidity)