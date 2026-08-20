import matplotlib.pyplot as plt
import config

ticks_duration = config.TICKS_DURATION

def run_graph(queue):

    spreads = []

    plt.ion()

    while True:

        try:

            spread = queue.get()

            spreads.append(spread)

            plt.clf()
            plt.plot(spreads)

            plt.title("Spread Mean")

            plt.pause(ticks_duration)

        except Exception as e:

            print("Graph Error:", e)