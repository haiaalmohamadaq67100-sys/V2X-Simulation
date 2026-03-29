"""
Network Statistics Manager
Tracks delays and session durations for MCM communication.
"""

import time
import logging

logger = logging.getLogger(__name__)


class NetworkStats:

    def __init__(self):

        # store timestamps of requests
        self.request_times = {}

        # store timestamps of session start
        self.session_start_times = {}

        # statistics
        self.request_response_delays = []
        self.session_durations = []
        self.cam_sent_times = {}
        self.cam_delays = []

    # ---------------------------------------
    # REQUEST generated
    # ---------------------------------------
    def record_request(self, manoeuvre_id):

        now = time.time()

        self.request_times[manoeuvre_id] = now
        self.session_start_times[manoeuvre_id] = now

    # ---------------------------------------
    # RESPONSE received
    # ---------------------------------------
    def record_response(self, manoeuvre_id):

        now = time.time()

        if manoeuvre_id in self.request_times:

            delay = now - self.request_times[manoeuvre_id]
            self.request_response_delays.append(delay)

            logger.info(
                f"[MCM] Request → Response delay = {delay:.3f} s"
            )


    # ---------------------------------------
    # TERMINATION received
    # ---------------------------------------
    def record_termination(self, manoeuvre_id):

        now = time.time()

        if manoeuvre_id in self.session_start_times:

            duration = now - self.session_start_times[manoeuvre_id]
            self.session_durations.append(duration)

            logger.info(
                f"[MCM] Session duration = {duration:.3f} s"
            )
    # ---------------------------------------
    # CAM SENT
    # ---------------------------------------
    def record_cam_sent(self, station_id):

        import time
        now = time.time()

        self.cam_sent_times[station_id] = now


    # ---------------------------------------
    # CAM RECEIVED
    # ---------------------------------------
    def record_cam_received(self, station_id):

        import time
        now = time.time()

        if station_id in self.cam_sent_times:

            delay = now - self.cam_sent_times[station_id]
            self.cam_delays.append(delay)

            logger.info(f"[CAM] delay = {delay:.3f} s")
    # ---------------------------------------
    # PRINT FINAL RESULTS
    # ---------------------------------------
    def print_summary(self):

        logger.info("=== MCM SESSION STATISTICS ===")

        if self.request_response_delays:

            avg = sum(self.request_response_delays) / len(self.request_response_delays)

            logger.info(
                f"Average Request → Response delay: {avg:.3f} s"
            )

        if self.session_durations:

            avg = sum(self.session_durations) / len(self.session_durations)

            logger.info(
                f"Average MCM session duration: {avg:.3f} s"
            )
        if self.cam_delays:

            avg = sum(self.cam_delays) / len(self.cam_delays)

            logger.info(f"Average CAM delay: {avg:.3f} s")

# global instance
network_stats = NetworkStats()
