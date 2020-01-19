import HABApp
from HABApp.openhab.events import ItemStateEvent
from HABApp.mqtt.items import MqttItem


class ExampleOpenhabToMQTTRule(HABApp.Rule):
    """This Rule mirrors all updates from OpenHAB to MQTT"""

    def __init__(self):
        super().__init__()

        for item in HABApp.core.Items.get_all_items():
            if isinstance(item, MqttItem):
                continue
            self.listen_event(item, self.process_update, ItemStateEvent)

    def process_update(self, event):
        assert isinstance(event, ItemStateEvent)

        print( f'/openhab/{event.name} <- {event.value}')
        self.mqtt.publish( f'/openhab/{event.name}', str(event.value))


ExampleOpenhabToMQTTRule()
