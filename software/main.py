import os
import platform
#import requests
#import numpy as np
#import sys
from rtlsdr import RtlSdr

import hashlib
from uuid import getnode as get_mac

import json
import time

# import multiprocessing
from multiprocessing import Process, Lock


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
    f = open(filename, 'wb')
    f.write(samples)
    f.close()
    os.rename(path_storing + filename, path_storing + filename + ".dat")

def run(path_storing, device):
    print("you are using", platform.system(), platform.release(), os.name)

    print("your groundstation id is", get_groundstationid())

    #device = 0
    rs = 2000000
    cf = 100000000
    ns = rs * 20
    gain = "auto"

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
    device = 0
    path_storing = ""
    run(path_storing, device)
