import utime
import machine
import dht
import uasyncio
import time
import _thread

import network
import requests
import socket
import ujson
import time

async def CommunicateWithClassifier():
    global currentTemperature, normalizedMoistureValue, loopRate
    ssid = '<networkName>'
    password = '<password>'
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid,password)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        await uasyncio.sleep(1)

    if wlan.status() !=  3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print( 'ip = ' + status[0] )
    
    while True:
        elapsedTime = 0
        try:
            startTime = utime.ticks_ms()
            tempF = (currentTemperature * (9/5)) + 32
            dataStr = str(tempF) + "," + str(normalizedMoistureValue)
            url = "http://<IP>:8000/prediction?data=" + dataStr
            response = requests.get(url)
            response_data = ujson.loads(response.text)
            prediction = response_data.get("prediction")
            print(prediction)
            endTime = utime.ticks_ms()
            elapsedTime_ms = utime.ticks_diff(endTime,startTime)
        
        except KeyboardInterrupt:
            break
        
        await uasyncio.sleep_ms(5000) #((1/loopRate) * 1000) - float(elapsedTime_ms))
    return

async def PulseFans(pulseLength_ms):
    global fanPin, greenLEDPin

    startTime = utime.ticks_ms()
    currentTime = utime.ticks_ms()
    elapsedTime = 0
    while (elapsedTime < pulseLength_ms):
    
        fanPin.value(1)
        greenLEDPin.value(1)
        currentTime = utime.ticks_ms()
        elapsedTime = utime.ticks_diff(currentTime,startTime)
    
    fanPin.value(0)
    greenLEDPin.value(0)

    
async def control_temperature():
    global thermometer,fanPulseLengthGain, upperTempThreshold, lowerTempThreshold, desiredTemperature, tempFile, loopRate, currentTemperature
    
    # frequency is 1 pulse every 20 seconds. This is essentially very slow PWM
    # your system cant get more powerful than fan always on!
    
    while True:
        try:
            thermometer.measure()
            currentTemperature = thermometer.temperature()
            print(f"Temperature (C): {currentTemperature:.2f} (Desired: {desiredTemperature:.2f})")
            
            temperatureError = currentTemperature - desiredTemperature
            
            if (currentTemperature > upperTempThreshold):
                print("Engaging fan!\n")
                
                # set it up so that a 5 degree error produces a half saturated PWM
                # 10 second PWM signal, so this needs to be a gain of 2 * (1000 ms)
                

                pulseLength_ms = min((1/loopRate) * 1000, temperatureError * fanPulseLengthGain)
                tempErrorInFahrenheit = (temperatureError * (9/5)) + 32
                print(f"Temperature Error: {temperatureError}. Starting pulse: {pulseLength_ms} ms")
                
    
                #await uasyncio.gather(
                await PulseFans(pulseLength_ms),
                    #uasyncio.sleep(1/loopRate)
                #    )
                await uasyncio.sleep((1/loopRate) - (pulseLength_ms/1000))
                # log telemetry
                tempFile.write(str(currentTemperature) + "," + str(temperatureError) + "," + str(pulseLength_ms) + "\n")
                
            else:
                #print(f"Temperature error is {temperatureError:.2f}. Taking no action\n")
                await uasyncio.sleep(1/loopRate)
                # log telemetry
                tempFile.write(str(currentTemperature) + "," + str(temperatureError) + "," + str(0) + "\n")
                
            # TELEMETER HERE
            
            
        except KeyboardInterrupt:
            break
        
async def monitor_moisture():
    global moistureSensor, normalizeDrySoilThreshold, moistureFile, loopRate, normalizedMoistureValue
    
    while True:
        try:
            currentMoistureValue = moistureSensor.read_u16()
            
            # Per Keyestudio documentation (from 0 to 1023):
            # 0  ~300     dry soil
            # 300~700     humid soil
            # 700~950     in water
            
            normalizedMoistureValue = currentMoistureValue / 65535
            
            if (normalizedMoistureValue < normalizeDrySoilThreshold):
                yellowLEDPin.value(1)
            else:
                yellowLEDPin.value(0)
                
            print(f"Moisture: {normalizedMoistureValue} (Threshold: {normalizeDrySoilThreshold})")
                
            # log telemetry
            moistureFile.write(str(normalizedMoistureValue) + "," + str(yellowLEDPin.value()) + "\n")
            
            await uasyncio.sleep(1/loopRate)
        except KeyboardInterrupt:
            break
        
async def control_light():
    global growLightPin, photocell, growLightTriggerThreshold, lightFile, loopRate
    
    while True:
        try:
            currentLightLevel = photocell.read_u16() * (5/65535)
            print(f"Photocell (0-5V): {currentLightLevel} (Threshold: {growLightTriggerThreshold})")
            
            if (currentLightLevel < growLightTriggerThreshold):
                growLightPin.value(1)
                redLEDPin.value(1)
            else:
                growLightPin.value(0)
                redLEDPin.value(0)
                
            # log telemetry
            lightFile.write(str(currentLightLevel) + "," + str(growLightPin.value()) + "\n")
            
            await uasyncio.sleep(1/loopRate)
        except KeyboardInterrupt:
            break
    
    
async def control_greenhouse():
    await uasyncio.gather(
        uasyncio.create_task(control_temperature()),
        uasyncio.create_task(control_light()),
        uasyncio.create_task(monitor_moisture()),
        uasyncio.create_task(CommunicateWithClassifier())
        )
    
    
async def main():
    print("You are here")
    await control_greenhouse()
    
# ACTUATOR CONTROL PINS
fanPin = machine.Pin(0, machine.Pin.OUT) # GPIO pin for binary fan input
growLightPin = machine.Pin(1, machine.Pin.OUT) # GPIO pin for binary grow light input

redLEDPin = machine.Pin(2, machine.Pin.OUT) #GPIO pin for the indicator LED
yellowLEDPin = machine.Pin(3, machine.Pin.OUT) #GPIO pin for the indicator LED
greenLEDPin = machine.Pin(4, machine.Pin.OUT) #GPIO pin for the indicator LED

# SENSOR FEEDBACK PINS
thermometer = dht.DHT11(machine.Pin(16))
photocell = machine.ADC(26) # pin to read photocell measurements
moistureSensor = machine.ADC(27) # pin to read moistureSensorMeasurements

# TOP-LEVEL CONTROLLER SETTINGS ---------------------------------
# Temperature Loop----
upperTempThreshold = (78 - 32) * (5/9)
lowerTempThreshold = (75 - 32) * (5/9)
desiredTemperature = (upperTempThreshold+lowerTempThreshold) / 2
fanPulseLengthGain = 500 #1000
# Light Loop ---------
growLightTriggerThreshold = 4
# Moisture Loop ------
normalizeDrySoilThreshold = 300 / 1023
# ---------------------------------------------------------------

# Loop Rate
loopRate = 1/5 #hz

# Telemetry Files
tempFile = open('_TemperatureData.csv',"w")
moistureFile = open('_MoistureData.csv',"w")
lightFile = open('_LightData.csv',"w")

# Sensor Measurement Initialization
currentTemperature = 0
normalizedMoistureValue = 0

enableClassifierComms = True
    
uasyncio.run(main())

    

