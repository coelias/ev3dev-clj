import os
import time
import sys
import json
import threading

class Device:
    def __init__(self,path):
        self.path = path
        self.value=None

    def getattr(self,name, f=None):
        try:
            with open(os.path.join(self.path,name)) as fil:
                if f:
                    return f(fil.read().strip())
                else:
                    return fil.read().strip()
        except IOError:
            return None

    def update_value(self):
        newvalue=self.calculate_values()

        if newvalue != self.value:
            self.value=newvalue
            sys.stdout.write(str(self)+"\n")
            sys.stdout.flush()

    def vals8(self,fns=[int]*8):
        return [self.getattr("value{}".format(i), fns[i]) for i in range(8)]

class Sensor(Device):
    def __init__(self, *args):
        Device.__init__(self,*args)
        self.port = self.getattr("address",lambda x: int(x.split(":in")[1]))
        self.driver = self.getattr("driver_name")
        self.modes = set(self.getattr("modes", lambda x: x.split(" ")))

    def set_mode(self, mode):
        if mode in self.modes: 
            with open(os.path.join(self.path,"mode"), "w") as fil:
                fil.write(mode)

    def __str__(self):
        return json.dumps({"port": self.port, "sensor": self.NAME, "values": self.value, "mode": self.getattr("mode")})

class ColorSensor(Sensor):
    NAME="color"
    def __init__(self, *args):
        Sensor.__init__(self,*args)

    def calculate_values(self):
        return self.vals8()

class GyroSensor(Sensor):
    NAME="gyro"
    def __init__(self, *args):
        Sensor.__init__(self,*args)

    def calculate_values(self):
        return self.vals8()

class USSensor(Sensor):
    NAME="ultrasound"
    def __init__(self, *args):
        Sensor.__init__(self,*args)

    def calculate_values(self):
        return self.vals8()

class TouchSensor(Sensor):
    NAME="touch"
    def __init__(self, *args):
        Sensor.__init__(self,*args)

    def calculate_values(self):
        return self.vals8()

class DeviceFinder():
    DEVMAP = {"lego-ev3-gyro": GyroSensor,
              "lego-ev3-color": ColorSensor,
              "lego-ev3-us": USSensor,
              "lego-ev3-touch": TouchSensor}

    SENSORS_PATH="/sys/class/lego-sensor/"
    TACHO_MOTORS_PATH="/sys/class/tacho-motor/"

    def __init__(self):
        self.devs=[]
        self.portmap={}

    def findSensors(self):
        return [os.path.join(self.SENSORS_PATH,i) for i in os.listdir(self.SENSORS_PATH)]

    def findMotors(self):
        return [os.path.join(self.TACHO_MOTORS_PATH,i) for i in os.listdir(self.TACHO_MOTORS_PATH)]

    def findDevices(self):
        self.devs=[]
        self.portmap={}
        for i in self.findSensors()+self.findMotors():
            with open(os.path.join(i,"driver_name")) as f:
                dn=f.read().strip()
            if dn in self.DEVMAP:
                device = self.DEVMAP[dn](i)
                self.portmap[device.port]=device
                self.devs.append(self.DEVMAP[dn](i))

    def run_action(self,port, op, **kwargs):
        device = self.portmap[port]
        getattr(device,op)(**kwargs)


    def updateValues(self):
        for i in self.devs:
            i.update_value()



devs=DeviceFinder()
devs.findDevices()

SAMPLING=0.05
RUNNING=True

def print_info():
    global SAMPLING
    global RUNNING
    global devs
    while RUNNING:
        devs.updateValues()
        time.sleep(SAMPLING)

threading.Thread(target=print_info).start()


def process_action(data):
    sys.stdout.flush()
    try:
        data=json.loads(data)
    except:
        sys.stdout.write("; Input not a JSON: {}".format(data)
        sys.stdout.flush()
        return
    try:
        devs.run_action(**data)   
    except:
        sys.stdout.write("; Error with action = {}".format(data)
        sys.stdout.flush()



for i in sys.stdin:
    process_action(i)

RUNNING=False

