"""spectrum_fetcher.py

Thread Which Handles Receiving Spectrum Data

"""

import zmq
import numpy as np
from threading import Thread
from time import sleep
import time


class SpectrumThread(Thread):
    """
    Thread for Fetching Spectrum Data from GNU Radio via ZMQ PUB/SUB
    """

    def __init__(
        self, group=None, target=None, name=None, port=5560, history_length=1000
    ):
        """Initializer for the SpectrumThread

        Parameters
        ----------
        group : NoneType
            The ThreadGroup the Thread Belongs to (Currently Unimplemented in Python 3.8)
        target : callable
            Function that the Thread Should Run (Leave This Be For Command Sending)
        name : str
            Name of the Thread
        port : int
            Port of the Spectrum Data ZMQ PUB/SUB Socket
        history_length : int
            Max Length of Spectrum Data History List
        """
        super().__init__(group=group, target=target, name=name, daemon=True)
        self.history_length = history_length
        self.spectrum = None
        self.history = []
        self.port = port
        # whether or not continuous integration is enabled
        self.cont_int = False
        # number of times we have integrated already
        self.cont_int_counts = 0

    def run(self):
        """Grabs Samples From ZMQ, Converts them to Numpy, and Stores

        Returns
        -------
        None
        """
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:%s" % self.port)
        socket.subscribe("")
        while True:
            rec = socket.recv()
            var = np.frombuffer(rec, dtype="float32")
            if len(self.history) >= self.history_length:
                self.history.pop()
            self.history.insert(0, (time.time(), var))
            if self.cont_int:
                self.spectrum = np.average([self.spectrum, var],
                    axis=0, weights=[self.cont_int_counts, 1]
                )
                self.cont_int_counts += 1
            else:
                self.spectrum = var

    def set_cont_int(self, val):
        """Enable or Disable Continuous Integration, Resetting the Integration Counter

        Parameters
        ----------
        val : bool
            True If Continuous Integration Should Be Enabled, False Otherwise
        """
        self.cont_int_counts = 0
        self.cont_int = val

    def get_spectrum(self):
        """Return Most Recent Spectrum

        Returns
        -------
        self.spectrum : (N) ndarray
        """
        return self.spectrum

    def get_history(self):
        """Return Entire History List

        Returns
        -------
        [(int, ndarray)]
            Time and Numpy Spectrum Pairs History
        """
        return self.history.copy()


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    thread = SpectrumThread()
    thread.start()
    sleep(1)
    print(thread.get_spectrum())
    data = thread.get_spectrum()
    plt.hist(range(len(data)), range(len(data)), weights=data)
    plt.xlabel("Frequency")
    plt.ylabel("Power")
    plt.show()
