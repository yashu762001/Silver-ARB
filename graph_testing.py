import matplotlib.pyplot as plt
import time
import random

plt.ion()

data = []

while True:
    data.append(random.random())
    plt.clf()
    plt.plot(data)
    plt.pause(0.1)
    time.sleep(0.1)