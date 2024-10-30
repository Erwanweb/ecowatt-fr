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
        self.J0Message = "En attente"
        self.J1Value = 0
        self.J1Message = "En attente"
        self.J2Value = 0
        self.J2Message = "En attente"
        self.J3Value = 0
        self.J3Message = "En attente"
        self.NOW = datetime.now()
        self.HourNumber = 0
        self.ProdNow = 0
        Self.ProdType = ""
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
            self.EcoWattRequest = datetime.now() + timedelta(minutes=1) # make make a json Call every 10 minutes

            Domoticz.Debug("Checking fo RTE datas")
            RTEDatas = EcoWattAPI("")
            if RTEDatas :
                Domoticz.Debug("jsonFile signals = {}".format(RTEDatas))
                
                # Today Ecowat values
                self.J0Value = int(RTEDatas['signals'][0]['dvalue'])
                if self.J0Value == 2 :
                    self.J0Value = 3
                elif self.J0Value == 3 :
                    self.J0Value = 4
                else :
                    self.J0Value = 1
                self.J0Message = str(RTEDatas['signals'][0]['message'])
                Domoticz.Debug("today dvalue is {} and message {}".format(str(self.J0Value), str(self.J0Message)))

                # J+1 Ecowat values
                self.J1Value = int(RTEDatas['signals'][1]['dvalue'])
                if self.J1Value == 2:
                    self.J1Value = 3
                elif self.J1Value == 3:
                    self.J1Value = 4
                else:
                    self.J1Value = 1
                self.J1Message = str(RTEDatas['signals'][1]['message'])
                Domoticz.Debug("J+1 dvalue is {} and message {}".format(str(self.J1Value), str(self.J1Message)))

                # J+2 Ecowat values
                self.J2Value = int(RTEDatas['signals'][2]['dvalue'])
                if self.J2Value == 2:
                    self.J2Value = 3
                elif self.J2Value == 3:
                    self.J2Value = 4
                else:
                    self.J2Value = 1
                self.J2Message = str(RTEDatas['signals'][2]['message'])
                Domoticz.Debug("J+2 dvalue is {} and message {}".format(str(self.J2Value), str(self.J2Message)))

                # J+3 Ecowat values
                self.J3Value = int(RTEDatas['signals'][3]['dvalue'])
                if self.J3Value == 2:
                    self.J3Value = 3
                elif self.J3Value == 3:
                    self.J3Value = 4
                else:
                    self.J3Value = 1
                self.J3Message = str(RTEDatas['signals'][3]['message'])
                Domoticz.Debug("J+3 dvalue is {} and message {}".format(str(self.J3Value), str(self.J3Message)))

                # Check Prod type now
                self.NOW = datetime.now()
                HourNow = self.NOW
                self.HourNumber = int(HourNow.strftime("%-H"))
                self.ProdNow = int(RTEDatas['signals'][0]['values'][self.HourNumber]['hvalue'])
                Self.ProdType = "Test"
                Domoticz.Debug("J+2 dvalue is {} and message {}".format(str(self.ProdNow), str(self.Self.ProdType)))

                #Updating devices values
                Domoticz.Log("Updating Devices from RTE datas")
                Devices[1].Update(nValue=self.J0Value, sValue=str(self.J0Message))
                Devices[2].Update(nValue=self.J1Value, sValue=str(self.J1Message))
                Devices[3].Update(nValue=self.J2Value, sValue=str(self.J2Message))
                Devices[4].Update(nValue=self.J3Value, sValue=str(self.J3Message))



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

def DomoticzAPI(APICall):

    resultJson = None
    url = f"http://127.0.0.1:8080/json.htm?{parse.quote(APICall, safe='&=')}"
    try:
        Domoticz.Debug(f"Domoticz API request: {url}")
        req = request.Request(url)
        response = request.urlopen(req)
        if response.status == 200:
            resultJson = json.loads(response.read().decode('utf-8'))
            if resultJson.get("status") != "OK":
                Domoticz.Error(f"Domoticz API returned an error: status = {resultJson.get('status')}")
                resultJson = None
        else:
            Domoticz.Error(f"Domoticz API: HTTP error = {response.status}")
    except urllib.error.HTTPError as e:
        Domoticz.Error(f"HTTP error calling '{url}': {e}")
    except urllib.error.URLError as e:
        Domoticz.Error(f"URL error calling '{url}': {e}")
    except json.JSONDecodeError as e:
        Domoticz.Error(f"JSON decoding error: {e}")
    except Exception as e:
        Domoticz.Error(f"Error calling '{url}': {e}")

    return resultJson

def EcoWattAPI(APICall):

    Domoticz.Debug("EcoWatt local API Called...")
    RTEjsonData = None
    jsonFile = "/home/tools/onevar/ecowatt.json"
    # Check for ecowatt datas file
    if not os.path.isfile(jsonFile):
        Domoticz.Error(f"Can't find {jsonFile} file!")
        return
    else:
        Domoticz.Debug("RTE datas found")
    # Check for ecowatt datas
    with open(jsonFile) as EcoWattStream:
        try:
            RTEjsonData = json.load(EcoWattStream)
        except:
            Domoticz.Error(f"Error opening json ecowatt file !")
    return RTEjsonData

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