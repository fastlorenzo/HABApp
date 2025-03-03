import asyncio
import logging
import time
from typing import Optional

import HABApp
from HABApp.core.internals import uses_event_bus
from HABApp.core.wrapper import log_exception
from HABApp.openhab.errors import OpenhabDisconnectedError
from ._plugin import PluginBase

log = logging.getLogger('HABApp.openhab.ping')


event_bus = uses_event_bus()


class PingOpenhab(PluginBase):
    def __init__(self):
        self.ping_value: Optional[float] = None
        self.ping_sent: Optional[float] = None
        self.ping_new: Optional[float] = None

        self.listener: Optional[HABApp.core.internals.EventBusListener] = None

        self.fut_ping: Optional[asyncio.Future] = None

    def setup(self):
        HABApp.config.CONFIG.openhab.ping.subscribe_for_changes(self.cfg_changed)
        self.cfg_changed()

    def on_connect(self):
        if not self.IS_CONNECTED:
            return None

        if not HABApp.config.CONFIG.openhab.ping.enabled:
            return None

        # initialize
        self.ping_value = None
        self.ping_sent = None
        self.ping_new = None

        self.fut_ping = asyncio.create_task(self.async_ping())

    def on_disconnect(self):
        if self.fut_ping is not None:
            self.fut_ping.cancel()
            self.fut_ping = None

        log.debug('Ping stopped')

    def cfg_changed(self):
        self.on_disconnect()

        if self.listener is not None:
            self.listener.cancel()
            self.listener = None

        if not HABApp.config.CONFIG.openhab.ping.enabled:
            return None

        self.listener = HABApp.core.internals.EventBusListener(
            HABApp.config.CONFIG.openhab.ping.item,
            HABApp.core.internals.wrap_func(self.ping_received),
            HABApp.core.events.EventFilter(HABApp.openhab.events.ItemStateEvent)
        )
        event_bus.add_listener(self.listener)

        self.on_connect()

    async def ping_received(self, event: HABApp.openhab.events.ItemStateEvent):
        value = event.value
        if value != self.ping_value:
            return None

        # We only save take the first ping we get
        if self.ping_new is not None:
            return None

        self.ping_new = round((time.time() - self.ping_sent) * 1000, 1)


    @log_exception
    async def async_ping(self):
        await asyncio.sleep(3)

        log.debug('Ping started')
        try:
            while True:

                self.ping_value = self.ping_new
                self.ping_new = None
                self.ping_sent = time.time()

                await HABApp.openhab.interface_async.async_post_update(
                    HABApp.config.CONFIG.openhab.ping.item,
                    f'{self.ping_value:.1f}' if self.ping_value is not None else None
                )

                await asyncio.sleep(HABApp.config.CONFIG.openhab.ping.interval)

        except OpenhabDisconnectedError:
            pass


PLUGIN_PING = PingOpenhab.create_plugin()
