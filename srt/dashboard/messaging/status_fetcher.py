"""status_fetcher.py

Thread Which Handles Receiving Status Data

"""

import zmq
from threading import Thread
from time import sleep
import json


# there currently seems to be a lack of a better place to hold information on
# the current frequency units and similar parameters, so for now I will put them
# in the StatusThread class
class FrequencyUnits():

    def __init__(self, status_thread):
        # reference to status thread
        self.status_thread = status_thread
        # user's currently selected frequency unit
        self.unit_name = "MHz"
        # frequency of the unshifted emission (if velocity units are used)
        self.freq_emit_Hz = 0

    def set_freq_unit(self, unit, freq_emit_Hz=0):
        """Sets the Current Frequency Units

        Parameters
        ----------
        unit : str
            Name of the Unit
        freq_emit_Hz : float
            For km/s Units, Frequency of the Unshifted Emission
        """
        self.unit_name = unit
        print("setting frequency unit to", unit)
        if unit == "km/s" and freq_emit_Hz <= 0:
            raise ValueError("freq_emit_Hz must be positive")
        else:
            self.freq_emit_Hz = freq_emit_Hz

    def Hz_to_current(self, freq_Hz):
        """Converts to Currently Set Frequency Units

        Parameters
        ----------
        freq_Hz : float
            Frequency You Desire to Convert, in Hz

        Returns
        -------
        Frequency In Currently Set Units
        """
        if self.unit_name == "Hz":
            return freq_Hz
        elif self.unit_name == "kHz":
            return freq_Hz / 1E3
        elif self.unit_name == "MHz":
            return freq_Hz / 1E6
        elif self.unit_name == "GHz":
            return freq_Hz / 1E9
        elif self.unit_name == "km/s":
            # NOTE: the relativistic calculation ((f/f0)^2-1)/((f/f0)^2+1)
            # doesn't scale nicely (frequency bins don't demarcate uniform steps
            # in velocity), so we approximate to first order for efficient
            # plotting. Speed of light is 299792.46 km/s.
            # Also, we correct for vlsr (see object_tracker.py)
            return (self.status_thread.get_status()["vlsr"]
                + (freq_Hz / self.freq_emit_Hz - 1) * 299792.46
            )
        else:
            raise ValueError("Unknown unit: {}".format(self.freq_unit))

    def Hz_to_current_full(self, freq_Hz):
        """Like Hz_to_current, But Returns Full Quantity With Unit"""
        return self.Hz_to_current(freq_Hz) + " " + self.unit_name

    def Hz_to_current_cf_bw(self, cf_Hz, bw_Hz):
        """Converts Center Frequency and Bandwidth in Hz to Center Frequency and Bandwidth in
        Current Units

        Parameters
        ----------
        cf_Hz : float
            Center Frequency You Desire to Convert, in Hz

        Returns
        -------
        (Center Frequency, Bandwidth) In Currently Set Units
        """
        if self.unit_name == "km/s":
            return (
                self.status_thread.get_status()["vlsr"],
                bw_Hz / self.freq_emit_Hz * 299792.46
            )
        else:
            return (self.Hz_to_current(cf_Hz), self.Hz_to_current(bw_Hz))


class StatusThread(Thread):
    """
    Thread Which Handles Receiving Status Data
    """

    def __init__(self, group=None, target=None, name=None, port=5555):
        """Initializer for StatusThread

        Parameters
        ----------
        group : NoneType
            The ThreadGroup the Thread Belongs to (Currently Unimplemented in Python 3.8)
        target : callable
            Function that the Thread Should Run (Leave This Be For Command Sending)
        name : str
            Name of the Thread
        port : int
            Port of the Status Data ZMQ PUB/SUB Socket
        """
        super().__init__(group=group, target=target, name=name, daemon=True)
        self.status = None
        self.port = port
        self.freq_unit = FrequencyUnits(self)

    def run(self):
        """Grabs Most Recent Status From ZMQ and Stores

        Returns
        -------

        """
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:%s" % self.port)
        socket.subscribe("")
        while True:
            rec = socket.recv()
            dump = json.loads(rec)
            self.status = dump

    def get_status(self):
        """Return Most Recent Status Dictionary

        Returns
        -------
        dict
            Status Dictionary
        """
        return self.status


if __name__ == "__main__":
    thread = StatusThread()
    thread.start()
    sleep(1)
    print(thread.get_status())
