import os
import time
import sys
import json
import threading
from ev3dev2.sound import Sound

SND=Sound()

def play_music(notes):
    SND.tone(notes)

def play_audio(audio):
    os.system("aplay -q audios/"+audio+".wav")

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

    def setattr(self,name,value):
        with open(os.path.join(self.path,name), "w") as fil:
            fil.write(str(value))

    def update_value(self):
        newvalue=self.calculate_values()

        if newvalue != self.value:
            self.value=newvalue
            sys.stdout.write(str(self)+"\n")
            sys.stdout.flush()

    def vals8(self,fns=[int]*8):
        return [self.getattr("value{}".format(i), fns[i]) for i in range(8)]

class TachoMotor(Device):
    NAME="tacho"
    def __init__(self, *args):
        Device.__init__(self,*args)
        self.port = self.getattr("address",lambda x: x.split(":out")[1])

    def calculate_values(self):
        return {"state": self.getattr("state"), "speed": self.getattr("speed", int), "position": self.getattr("position",int)}

    def set_speed(self, speed):
        self.setattr("speed_sp",speed)

    def stop(self):
        self.setattr("command","stop")

    def stop_action(self, action):
        self.setattr("stop_action",action)

    def reset(self):
        self.setattr("command","reset")

    def run_timed(self,ms):
        self.setattr("time_sp",ms)
        self.setattr("command","run-times")

    def run_forever(self):
        self.setattr("command","run-forever")

    def run_to_abs_pos(self, pos):
        self.setattr("position_sp",pos)
        self.setattr("command","run-to-abs-pos")

    def run_to_rel_pos(self, pos):
        self.setattr("position_sp",pos)
        self.setattr("command","run-to-rel-pos")

    def __str__(self):
        data={"port": self.port, "motor": self.NAME, }
        data.update(self.value)
        return json.dumps(data)

class TachoDual(Device):
    NAME="tachoDual"
    def __init__(self, tacho1, tacho2):
        Device.__init__(self,"")
        self.path1 = tacho1.path
        self.path2 = tacho2.path

    def getattr(self,path, name, f=None):
        try:
            with open(os.path.join(path,name)) as fil:
                if f:
                    return f(fil.read().strip())
                else:
                    return fil.read().strip()
        except IOError:
            return None

    def setattr(self,name,value1, value2):
        with open(os.path.join(self.path1,name), "w") as fil:
            with open(os.path.join(self.path2,name), "w") as fil2:
                fil.write(str(value1))
                fil2.write(str(value2))

    def set_speed(self, speed1, speed2):
        self.setattr("speed_sp",speed1, speed2)

    def stop(self):
        self.setattr("command","stop", "stop")

    def stop_action(self, action):
        self.setattr("stop_action",action, action)

    def reset(self):
        self.setattr("command","reset","reset")

    def run_timed(self,ms):
        self.setattr("time_sp",ms,ms)
        self.setattr("command","run-timed","run-timed")

    def run_forever(self):
        self.setattr("command","run-forever","run-forever")

    def run_to_abs_pos(self, pos):
        self.setattr("position_sp",pos,pos)
        self.setattr("command","run-to-abs-pos","run-to-abs-pos")

    def run_to_rel_pos(self, pos, pos2=None):
        self.setattr("position_sp",pos,pos2 or pos)
        self.setattr("command","run-to-rel-pos","run-to-rel-pos")

    def __str__(self):
        data={"port": self.port, "motor": self.NAME, }
        data.update(self.value)
        return json.dumps(data)

class Sensor(Device):
    def __init__(self, *args):
        Device.__init__(self,*args)
        self.port = self.getattr("address",lambda x: int(x.split(":in")[1]))
        self.driver = self.getattr("driver_name")
        self.modes = set(self.getattr("modes", lambda x: x.split(" ")))

    def set_mode(self, mode):
        if mode in self.modes: 
            self.setattr("mode",mode)

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
              "lego-ev3-touch": TouchSensor,
              "lego-ev3-l-motor": TachoMotor}

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

        if self.portmap["A"] and self.portmap["A"].NAME=="tacho" and self.portmap["D"] and self.portmap["D"].NAME=="tacho":
               self.portmap["A,D"] = TachoDual(self.portmap["A"], self.portmap["D"])
               del self.portmap["A"]
               del self.portmap["D"]
                

    def run_action(self,op, port=None, delay=None, **kwargs):
        if op=="music":
            play_music(**kwargs)
        elif op=="audio":
            play_audio(**kwargs)
        else:
            device = self.portmap[port]
            getattr(device,op)(**kwargs)
            if delay:
                time.sleep(delay)


    def updateValues(self):
        for i in self.devs:
            i.update_value()



devs=DeviceFinder()
devs.findDevices()

SAMPLING=0.01
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
        sys.stdout.write("; Input not a JSON: {}".format(data))
        sys.stdout.flush()
        return
    try:
        if type(data) == list:
            for i in data:
                devs.run_action(**i)
        elif type(data) == dict:
            devs.run_action(**data)    
    except:
        sys.stdout.write("; Error with action = {}".format(data))
        sys.stdout.flush()



for i in sys.stdin:
    process_action(i)

RUNNING=False

