import json
from itertools import count

import backend.time_util as tu
from backend.config import Config
from backend.controller import Controller
from backend.logger import logger


class EventStream:

    PERIOD: float = Config.get_constant('event_stream_period')
    RETRY_PERIOD: float = Config.get_constant('event_stream_retry_period')

    def _retry_period_in_ms(self):
        return int(self.RETRY_PERIOD * 1000)

    def event_stream_handler(self):
        logger.info("Started event stream")
        for idx in count(start=0):
            tu.sleep(self.PERIOD)
            data = Controller.get_state()
            yield f"retry: {self._retry_period_in_ms()}\ndata: {json.dumps(data)}\nid: {str(idx)}\n\n"
