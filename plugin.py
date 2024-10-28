#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ecowatt plugin for Domoticz
# Author: MrErwan,
# Version:    0.0.1: alpha..

"""
<plugin key="ECOWATT-FR" name="Ecowatt RTE plugin from Ronelabs" author="Ronelabs" version="0.0.2" externallink="https://github.com/Erwanweb/ecowatt-fr.git">
      <description>
        <h2>Ecowatt RTE plugin from Ronelabs</h2><br/>
        Easily implement in Domoticz Ecowatt RTE's datas<br/>
        <h3>Set-up and Configuration</h3>
    </description>
    <params>
        <param field="Mode6" label="Logging Level" width="200px">
            <options>
                <option label="Normal" value="Normal"  default="true"/>
                <option label="Verbose" value="Verbose"/>
                <option label="Debug - Python Only" value="2"/>
                <option label="Debug - Basic" value="62"/>
                <option label="Debug - Basic+Messages" value="126"/>
                <option label="Debug - Connections Only" value="16"/>
                <option label="Debug - Connections+Queue" value="144"/>
                <option label="Debug - All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import urllib.parse as parse
import urllib.request as request
from datetime import datetime, timedelta
import time
import math
import base64
import itertools
import requests
import subprocess
import os
from typing import Any

try:
    from Domoticz import Devices, Images, Parameters, Settings
except ImportError:
    pass

class deviceparam:

    def __init__(self, unit, nvalue, svalue):
        self.unit = unit
        self.nvalue = nvalue
        self.svalue = svalue


class BasePlugin:

    def __init__(self):

        self.debug = False
        self.EcoWattRequest = datetime.now()
        self.J0Value = 0
        self.J0Message = "Pas d’alerte."
        return


    def onStart(self):

        # setup the appropriate logging level
        try:
            debuglevel = int(Parameters["Mode6"])
        except ValueError:
            debuglevel = 0
            self.loglevel = Parameters["Mode6"]
        if debuglevel != 0:
            self.debug = True
            Domoticz.Debugging(debuglevel)
            DumpConfigToLog()
            self.loglevel = "Verbose"
        else:
            self.debug = False
            Domoticz.Debugging(0)

        # create the child devices if these do not exist yet
        devicecreated = []
        if 1 not in Devices:
            Domoticz.Device(Name="Aujourd'hui", Unit=1, TypeName="Alert", Used=1).Create()
            devicecreated.append(deviceparam(1, 0, ""))  # default is clear
        if 2 not in Devices:
            Domoticz.Device(Name="J+1", Unit=2, TypeName="Alert", Used=1).Create()
            devicecreated.append(deviceparam(2, 0, ""))  # default is clear
        if 3 not in Devices:
            Domoticz.Device(Name="J+2", Unit=3, TypeName="Alert", Used=1).Create()
            devicecreated.append(deviceparam(3, 0, ""))  # default is clear
        if 4 not in Devices:
            Domoticz.Device(Name="J+3", Unit=4, TypeName="Alert", Used=1).Create()
            devicecreated.append(deviceparam(4, 0, ""))  # default is clear


        # if any device has been created in onStart(), now is time to update its defaults
        for device in devicecreated:
            Devices[device.unit].Update(nValue=device.nvalue, sValue=device.svalue)

        # Set domoticz heartbeat to 20 s (onheattbeat() will be called every 20 )
        Domoticz.Heartbeat(20)

    def onStop(self):

        Domoticz.Debugging(0)


    def onCommand(self, Unit, Command, Level, Color):

        Domoticz.Debug("onCommand called for Unit {}: Command '{}', Level: {}".format(Unit, Command, Level))

    def onHeartbeat(self):

        Domoticz.Debug("onHeartbeat Called...")

        now = datetime.now()

        if self.EcoWattRequest <= now:
            #WeatherMapAPI("")
            self.EcoWattRequest = datetime.now() + timedelta(minutes=1) # make make a json Call every 10 minutes

            Domoticz.Debug("Checking fo RTE datas")
            jsonData = None
            jsonFile = "/home/tools/onevar/ecowatt.json"
            # jsonFile = "/home/tools/onevar/ecowatt.json"
            # Check for ecowatt datas file
            if not os.path.isfile(jsonFile):
                Domoticz.Error(f"Can't find {jsonFile} file!")
                return
            else :
                Domoticz.Debug("RTE datas found")

            with open(jsonFile, encoding='UTF-8') as EcoWattStream:
                try:
                    #jsonData = json.load(EcoWattStream)
                    jsonData = json.loads(EcoWattStream.read().decode('utf-8'))
                except:
                    Domoticz.Error(f"Error opening json ecowatt file !")
                    return

            #if jsonData:
                #Domoticz.Debug("RTE datas received")
                #self.J0Value = int(jsonData['signals'][0]['dvalue'])
                #Domoticz.Debug("signal dvalue d0 = {}".format(self.J0Value))
                    """if self.J0Value > 1 :
                        self.J0Value = self.J0Value + 1
                    else :
                        self.J0Value = 1
                self.J0Message = str(jsonData['signals'][0]['message'])"""

                #Updating devices values
                #Domoticz.Debug("Updating Devices from RTE datas")
                #Devices[1].Update(nValue= self.J0Value, sValue=str(self.J0Message))



global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onCommand(Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Color)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Plugin utility functions ---------------------------------------------------

def parseCSV(strCSV):
    listvals = []
    for value in strCSV.split(","):
        try:
            val = int(value)
            listvals.append(val)
        except ValueError:
            try:
                val = float(value)
                listvals.append(val)
            except ValueError:
                Domoticz.Error(f"Skipping non-numeric value: {value}")
    return listvals


def CheckParam(name, value, default):

    try:
        param = int(value)
    except ValueError:
        param = default
        Domoticz.Error("Parameter '{}' has an invalid value of '{}' ! defaut of '{}' is instead used.".format(name, value, default))
    return param


# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return