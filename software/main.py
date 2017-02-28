import os
import platform
#import requests
#import numpy as np
#import sys
from rtlsdr import RtlSdr, librtlsdr

import hashlib
from uuid import getnode as get_mac

import json
import time

# import multiprocessing
from multiprocessing import Process, Lock


def create_config():
    sdrconfig = { "sdr":
            [
                {
                    "name": "rtlsdr",
                    "type": "rtlsdr",
                    "center_frequency": 1090000000,
                    "samplerate": 2000000,
                    "gain_fixed": "auto",
                    "gain_auto_range": [0, 50],
                    "gain_auto_threshold": 0.3,
                    "frequency_correction": 0,
                    "mode": "",
                    "timer": [100000, 200000],
                    "recording_time": 90
                }
            ]
            }

    # Writing JSON data
    with open('sdr_config.json', 'w') as f:
        json.dump(sdrconfig, f, indent=4)


def do_sha224(x):
    hashed = hashlib.sha224(x)
    hashed = hashed.hexdigest()
    return hashed

def get_groundstationid():
    filename = "my_groundstationid.json"
    if os.path.exists(filename):
        # Reading data back
        with open(filename, 'r') as f:
            data = json.load(f)
        id = data["my_groundstationid"]
        #print("loaded id", id)
    else:
        id = do_sha224(str(get_mac()).encode("utf-8"))  # added .encode("utf-8") for python 3.4.3
        data = {"my_groundstationid" : id}
        #print(data)

        # Writing JSON data
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        #np.save("groundstationid.npy", id)

    #print("your groundstation id is", id)
    return id

def storing_stream_with_windows(lock, rs, cf, gain, ns, device, path_storing):

    if librtlsdr.rtlsdr_get_device_count() > 0:
        lock.acquire()
        sdr = RtlSdr(device_index = device)

        # some defaults
        sdr.rs = rs
        sdr.fc = cf
        sdr.gain = gain

        samples = sdr.read_bytes(ns * 2)
        sdr.close()

        lock.release()
    #print("print")

        filename = get_groundstationid() + "_f" + str(cf) + "_d" + str(device) + "_t" + str(int(time.time()))
        f = open(path_storing + filename + ".tmp", 'wb')
        f.write(samples)
        f.close()
        os.rename(path_storing + filename + ".tmp", path_storing + filename + ".dat")

def run(path_storing, path_ops, path_logs, device):
    print("you are using", platform.system(), platform.release(), os.name)

    print("your groundstation id is", get_groundstationid())

    print("loading configs from", path_ops + "sdr_config.json", "for device", device)
    with open(path_ops + 'sdr_config.json', 'r') as f:
         sdr_configuration = json.load(f)
    print(sdr_configuration)

    #device = 0
    rs   = sdr_configuration["sdr"][0]["samplerate"]
    cf   = sdr_configuration["sdr"][0]["center_frequency"]
    ns   = sdr_configuration["sdr"][0]["recording_time"] * rs
    gain = sdr_configuration["sdr"][0]["gain_fixed"]

    #print(test.update(nsamples))


    if platform.system() == "Windows":
        # preparing the multiprocess for recordings
        lock = Lock()
        jobs = []

        for recs in range(2):
            p = Process(target=storing_stream_with_windows, args=(lock, rs, cf, gain, ns, device, path_storing))
            jobs.append(p)
            p.start()
            #print("end")

        while True == True:
            time.sleep(2)
            for n, p in enumerate(jobs):
                if not p.is_alive():
                    jobs.pop(n)
                    recs += 1
                    p = Process(target=storing_stream_with_windows, args=(lock, rs, cf, gain, ns, device, path_storing))
                    jobs.append(p)
                    p.start()
                    print("rec number", recs, 'added')

if __name__ == '__main__':
    #create_config()
    device = 0
    path_storing = ""
    path_ops = ""
    path_logs = ""
    run(path_storing, path_ops, path_logs, device)
