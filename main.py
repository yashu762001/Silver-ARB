import multiprocessing as mp
from multiprocessing import Process, Queue
import ui
import strategy_runner
import graph_plotter
import sys
from strategy_parameters import params


if __name__ == "__main__":
    manager = mp.Manager()
    shared_params = manager.dict(params)

    graph_queue = Queue()

    ui_process = Process(target=ui.run_ui, args=(shared_params,))

    strategy_process = Process(
        target=strategy_runner.run_strategy,
        args=(graph_queue,shared_params)
    )

    graph_process = Process(
        target=graph_plotter.run_graph,
        args=(graph_queue,)
    )

    ui_process.start()
    sys.stderr.write("ui started\n")
    sys.stderr.flush()
    strategy_process.start()
    sys.stderr.write("strategy started\n")
    sys.stderr.flush()
    graph_process.start()
    sys.stderr.write("graph started\n")
    sys.stderr.flush()

    ui_process.join()
    strategy_process.join()
    graph_process.join()