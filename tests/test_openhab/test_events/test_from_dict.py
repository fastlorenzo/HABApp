import datetime
import pytest

from HABApp.openhab.events import ChannelTriggeredEvent, GroupItemStateChangedEvent, ItemAddedEvent, ItemCommandEvent, \
    ItemStateChangedEvent, ItemStateEvent, ItemStatePredictedEvent, ItemUpdatedEvent, ThingConfigStatusInfoEvent, \
    ThingStatusInfoChangedEvent, ThingStatusInfoEvent, ThingFirmwareStatusInfoEvent, ChannelDescriptionChangedEvent, \
    ThingAddedEvent, ThingRemovedEvent
from HABApp.openhab.map_events import get_event, EVENT_LIST


def test_ItemStateEvent():
    event = get_event({'topic': 'openhab/items/Ping/state', 'payload': '{"type":"String","value":"1"}',
                       'type': 'ItemStateEvent'})
    assert isinstance(event, ItemStateEvent)
    assert event.name == 'Ping'
    assert event.value == '1'

    event = get_event({'topic': 'openhab/items/my_item_name/state',
                       'payload': '{"type":"String","value":"NONE"}', 'type': 'ItemStateEvent'})
    assert isinstance(event, ItemStateEvent)
    assert event.name == 'my_item_name'
    assert event.value is None


def test_ItemCommandEvent():
    event = get_event({'topic': 'openhab/items/Ping/command', 'payload': '{"type":"String","value":"1"}',
                       'type': 'ItemCommandEvent'})
    assert isinstance(event, ItemCommandEvent)
    assert event.name == 'Ping'
    assert event.value == '1'


def test_ItemAddedEvent1():
    event = get_event({'topic': 'openhab/items/TestString/added',
                       'payload': '{"type":"String","name":"TestString","tags":[],"groupNames":["TestGroup"]}',
                       'type': 'ItemAddedEvent'})
    assert isinstance(event, ItemAddedEvent)
    assert event.name == 'TestString'
    assert event.type == 'String'


def test_ItemAddedEvent2():
    event = get_event({
        'topic': 'openhab/items/TestColor_OFF/added',
        'payload': '{"type":"Color","name":"TestColor_OFF","tags":[],"groupNames":["TestGroup"]}',
        'type': 'ItemAddedEvent'
    })
    assert isinstance(event, ItemAddedEvent)
    assert event.name == 'TestColor_OFF'
    assert event.type == 'Color'
    assert event.tags == frozenset()
    assert event.groups == frozenset(["TestGroup"])
    assert str(event) == '<ItemAddedEvent name: TestColor_OFF, type: Color, tags:, groups: {TestGroup}>'

    event = get_event({
        'topic': 'openhab/items/TestColor_OFF/added',
        'payload': '{"type":"Color","name":"TestColor_OFF","tags":["test_tag","tag2"],"groupNames":["TestGroup"]}',
        'type': 'ItemAddedEvent'
    })
    assert isinstance(event, ItemAddedEvent)
    assert event.name == 'TestColor_OFF'
    assert event.type == 'Color'
    assert event.tags == frozenset(['test_tag', 'tag2'])
    assert event.groups == frozenset(['TestGroup'])

    assert str(event) == '<ItemAddedEvent name: TestColor_OFF, type: Color, ' \
                         'tags: {tag2, test_tag}, groups: {TestGroup}>'


def test_ItemUpdatedEvent():
    event = get_event({
        'topic': 'openhab/items/NameUpdated/updated',
        'payload': '[{"type":"Switch","name":"Test","tags":[],"groupNames":[]},'
                   '{"type":"Contact","name":"Test","tags":[],"groupNames":[]}]',
        'type': 'ItemUpdatedEvent'
    })
    assert isinstance(event, ItemUpdatedEvent)
    assert event.name == 'NameUpdated'
    assert event.type == 'Switch'
    assert event.tags == frozenset()
    assert event.groups == frozenset()
    assert str(event) == '<ItemUpdatedEvent name: NameUpdated, type: Switch, tags:, groups:>'

    event = get_event({
        'topic': 'openhab/items/NameUpdated/updated',
        'payload': '[{"type":"Switch","name":"Test","tags":["tag5","tag1"],"groupNames":["def","abc"]},'
                   '{"type":"Contact","name":"Test","tags":[],"groupNames":[]}]',
        'type': 'ItemUpdatedEvent'
    })
    assert isinstance(event, ItemUpdatedEvent)
    assert event.name == 'NameUpdated'
    assert event.type == 'Switch'
    assert event.tags == frozenset(['tag1', 'tag5'])
    assert event.groups == frozenset(['abc', 'def'])
    assert str(event) == '<ItemUpdatedEvent name: NameUpdated, type: Switch, tags: {tag1, tag5}, groups: {abc, def}>'


def test_ItemStateChangedEvent1():
    event = get_event({'topic': 'openhab/items/Ping/statechanged',
                       'payload': '{"type":"String","value":"1","oldType":"UnDef","oldValue":"NULL"}',
                       'type': 'ItemStateChangedEvent'})
    assert isinstance(event, ItemStateChangedEvent)
    assert event.name == 'Ping'
    assert event.value == '1'
    assert event.old_value is None


def test_ItemStatePredictedEvent():
    event = get_event({'topic': 'openhab/items/Buero_Lampe_Vorne_W/statepredicted',
                       'payload': '{"predictedType":"Percent","predictedValue":"10","isConfirmation":false}',
                       'type': 'ItemStatePredictedEvent'})
    assert isinstance(event, ItemStatePredictedEvent)
    assert event.name == 'Buero_Lampe_Vorne_W'
    assert event.value.value == 10.0


def test_ItemStateChangedEvent2():
    UTC_OFFSET = datetime.datetime.now().astimezone(None).strftime('%z')

    _in = {
        'topic': 'openhab/items/TestDateTimeTOGGLE/statechanged',
        'payload': f'{{"type":"DateTime","value":"2018-06-21T19:47:08.000{UTC_OFFSET}",'
                   f'"oldType":"DateTime","oldValue":"2017-10-20T17:46:07.000{UTC_OFFSET}"}}',
        'type': 'ItemStateChangedEvent'}

    event = get_event(_in)

    assert isinstance(event, ItemStateChangedEvent)
    assert event.name == 'TestDateTimeTOGGLE'
    assert datetime.datetime(2018, 6, 21, 19, 47, 8), event.value


def test_GroupItemStateChangedEvent():
    d = {
        'topic': 'openhab/items/TestGroupAVG/TestNumber1/statechanged',
        'payload': '{"type":"Decimal","value":"16","oldType":"Decimal","oldValue":"15"}',
        'type': 'GroupItemStateChangedEvent'
    }
    event = get_event(d)
    assert isinstance(event, GroupItemStateChangedEvent)
    assert event.name == 'TestGroupAVG'
    assert event.item == 'TestNumber1'
    assert event.value == 16
    assert event.old_value == 15


def test_channel_ChannelTriggeredEvent():
    d = {
        "topic": "openhab/channels/mihome:sensor_switch:00000000000000:button/triggered",
        "payload": "{\"event\":\"SHORT_PRESSED\",\"channel\":\"mihome:sensor_switch:11111111111111:button\"}",
        "type": "ChannelTriggeredEvent"
    }

    event = get_event(d)
    assert isinstance(event, ChannelTriggeredEvent)
    assert event.name == 'mihome:sensor_switch:00000000000000:button'
    assert event.channel == 'mihome:sensor_switch:11111111111111:button'
    assert event.event == 'SHORT_PRESSED'


def test_channel_ChannelDescriptionChangedEvent():
    data = {
        'topic': 'openhab/channels/lgwebos:WebOSTV:**********************:channel/descriptionchanged',
        'payload': '{"field":"STATE_OPTIONS","channelUID":"lgwebos:WebOSTV:**********************:channel",'
                   '"linkedItemNames":[],"value":"{\\"options\\":[]}"}',
        'type': 'ChannelDescriptionChangedEvent'
    }
    event = get_event(data)
    assert isinstance(event, ChannelDescriptionChangedEvent)
    assert event.name == 'lgwebos:WebOSTV:**********************:channel'
    assert event.field == 'STATE_OPTIONS'
    assert event.value == '{"options":[]}'


def test_thing_ThingStatusInfoEvent():
    data = {
        'topic': 'openhab/things/samsungtv:tv:mysamsungtv/status',
        'payload': '{"status":"ONLINE","statusDetail":"MyStatusDetail"}',
        'type': 'ThingStatusInfoEvent'
    }
    event = get_event(data)
    assert isinstance(event, ThingStatusInfoEvent)
    assert event.name == 'samsungtv:tv:mysamsungtv'
    assert event.status == 'ONLINE'
    assert event.detail == 'MyStatusDetail'

    data = {
        'topic': 'openhab/things/chromecast:chromecast:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/status',
        'payload': '{"status":"ONLINE","statusDetail":"NONE"}',
        'type': 'ThingStatusInfoEvent'
    }
    event = get_event(data)
    assert isinstance(event, ThingStatusInfoEvent)
    assert event.name == 'chromecast:chromecast:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    assert event.status == 'ONLINE'
    assert event.detail is None


def test_thing_ThingStatusInfoChangedEvent():
    data = {
        'topic': 'openhab/things/samsungtv:tv:mysamsungtv/statuschanged',
        'payload': '[{"status":"OFFLINE","statusDetail":"NONE"},{"status":"ONLINE","statusDetail":"NONE"}]',
        'type': 'ThingStatusInfoChangedEvent'
    }
    event = get_event(data)
    assert isinstance(event, ThingStatusInfoChangedEvent)
    assert event.name == 'samsungtv:tv:mysamsungtv'
    assert event.status == 'OFFLINE'
    assert event.detail is None
    assert event.old_status == 'ONLINE'
    assert event.old_detail is None


def test_thing_ConfigStatusInfoEvent():
    data = {
        'topic': 'openhab/things/zwave:device:controller:my_node/config/status',
        'payload': '{"configStatusMessages":[{"parameterName":"switchall_mode","type":"PENDING"}]}',
        'type': 'ConfigStatusInfoEvent'
    }
    event = get_event(data)
    assert isinstance(event, ThingConfigStatusInfoEvent)
    assert event.name == 'zwave:device:controller:my_node'
    assert event.messages == [{"parameterName": "switchall_mode", "type": "PENDING"}]


def test_thing_FirmwareStatusEvent():
    data = {
        'topic': 'openhab/things/zigbee:device:12345678:9abcdefghijklmno/firmware/status',
        'payload':
            '{"thingUID":{"segments":["zigbee","device","12345678","9abcdefghijklmno"]},"firmwareStatus":"UNKNOWN"}',
        'type': 'FirmwareStatusInfoEvent'
    }
    event = get_event(data)
    assert isinstance(event, ThingFirmwareStatusInfoEvent)
    assert event.status == 'UNKNOWN'


def test_thing_ThingAddedEvent():
    data = {
        'topic': 'openhab/things/astro:sun:0a94363608/added',
        'payload': '{"channels":[{"uid":"astro:sun:0a94363608:rise#start","id":"rise#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:rise#end","id":"rise#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:rise#duration","id":"rise#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:rise#event","id":"rise#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:set#start","id":"set#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:set#end","id":"set#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:set#duration","id":"set#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:set#event","id":"set#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:noon#start","id":"noon#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:noon#end","id":"noon#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:noon#duration","id":"noon#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:noon#event","id":"noon#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:night#start","id":"night#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:night#end","id":"night#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:night#duration","id":"night#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:night#event","id":"night#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:morningNight#start","id":"morningNight#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:morningNight#end","id":"morningNight#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:morningNight#duration","id":"morningNight#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:morningNight#event","id":"morningNight#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDawn#start","id":"astroDawn#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDawn#end","id":"astroDawn#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDawn#duration","id":"astroDawn#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:astroDawn#event","id":"astroDawn#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDawn#start","id":"nauticDawn#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDawn#end","id":"nauticDawn#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDawn#duration","id":"nauticDawn#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:nauticDawn#event","id":"nauticDawn#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDawn#start","id":"civilDawn#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDawn#end","id":"civilDawn#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDawn#duration","id":"civilDawn#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:civilDawn#event","id":"civilDawn#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDusk#start","id":"astroDusk#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDusk#end","id":"astroDusk#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDusk#duration","id":"astroDusk#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:astroDusk#event","id":"astroDusk#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDusk#start","id":"nauticDusk#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDusk#end","id":"nauticDusk#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDusk#duration","id":"nauticDusk#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:nauticDusk#event","id":"nauticDusk#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDusk#start","id":"civilDusk#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDusk#end","id":"civilDusk#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDusk#duration","id":"civilDusk#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:civilDusk#event","id":"civilDusk#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:eveningNight#start","id":"eveningNight#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:eveningNight#end","id":"eveningNight#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:eveningNight#duration","id":"eveningNight#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eveningNight#event","id":"eveningNight#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:daylight#start","id":"daylight#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:daylight#end","id":"daylight#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:daylight#duration","id":"daylight#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:daylight#event","id":"daylight#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:position#azimuth","id":"position#azimuth","channelTypeUID":"astro:azimuth","itemType":"Number:Angle","kind":"STATE","label":"Azimut","description":"Das Azimut des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:position#elevation","id":"position#elevation","channelTypeUID":"astro:elevation","itemType":"Number:Angle","kind":"STATE","label":"Höhenwinkel","description":"Der Höhenwinkel des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:position#shadeLength","id":"position#shadeLength","channelTypeUID":"astro:shadeLength","itemType":"Number","kind":"STATE","label":"Schattenlängenverhältnis","description":"Projiziertes Schattenlängenverhältnis (Abgeleitet vom Höhenwinkel)","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:radiation#direct","id":"radiation#direct","channelTypeUID":"astro:directRadiation","itemType":"Number:Intensity","kind":"STATE","label":"Direkte Strahlung","description":"Höhe der Strahlung nach Eindringen in die atmosphärische Schicht","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:radiation#diffuse","id":"radiation#diffuse","channelTypeUID":"astro:diffuseRadiation","itemType":"Number:Intensity","kind":"STATE","label":"Diffuse Strahlung","description":"Höhe der Strahlung, nach Beugung durch Wolken und Atmosphäre","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:radiation#total","id":"radiation#total","channelTypeUID":"astro:totalRadiation","itemType":"Number:Intensity","kind":"STATE","label":"Gesamtstrahlung","description":"Gesamtmenge der Strahlung auf dem Boden","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:zodiac#start","id":"zodiac#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:zodiac#end","id":"zodiac#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:zodiac#sign","id":"zodiac#sign","channelTypeUID":"astro:sign","itemType":"String","kind":"STATE","label":"Sternzeichen","description":"Das Sternzeichen","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#name","id":"season#name","channelTypeUID":"astro:seasonName","itemType":"String","kind":"STATE","label":"Jahreszeit","description":"Der Name der aktuellen Jahreszeit","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#spring","id":"season#spring","channelTypeUID":"astro:spring","itemType":"DateTime","kind":"STATE","label":"Frühling","description":"Frühlingsanfang","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#summer","id":"season#summer","channelTypeUID":"astro:summer","itemType":"DateTime","kind":"STATE","label":"Sommer","description":"Sommeranfang","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#autumn","id":"season#autumn","channelTypeUID":"astro:autumn","itemType":"DateTime","kind":"STATE","label":"Herbst","description":"Herbstanfang","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#winter","id":"season#winter","channelTypeUID":"astro:winter","itemType":"DateTime","kind":"STATE","label":"Winter","description":"Winteranfang","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#nextName","id":"season#nextName","channelTypeUID":"astro:seasonName","itemType":"String","kind":"STATE","label":"Nächste Jahreszeit","description":"Der Name der nächsten Jahreszeit","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#timeLeft","id":"season#timeLeft","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Verbleibende Zeit","description":"Die verbleibende Zeit bis zum nächsten Jahreszeitwechsel","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#total","id":"eclipse#total","channelTypeUID":"astro:total","itemType":"DateTime","kind":"STATE","label":"Totale Sonnenfinsternis","description":"Zeitpunkt der nächsten totalen Sonnenfinsternis","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#totalElevation","id":"eclipse#totalElevation","channelTypeUID":"astro:elevation","itemType":"Number:Angle","kind":"STATE","label":"Höhenwinkel","description":"Der Höhenwinkel des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#partial","id":"eclipse#partial","channelTypeUID":"astro:partial","itemType":"DateTime","kind":"STATE","label":"Partielle Sonnenfinsternis","description":"Zeitpunkt der nächsten partiellen Sonnenfinsternis","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#partialElevation","id":"eclipse#partialElevation","channelTypeUID":"astro:elevation","itemType":"Number:Angle","kind":"STATE","label":"Höhenwinkel","description":"Der Höhenwinkel des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#ring","id":"eclipse#ring","channelTypeUID":"astro:ring","itemType":"DateTime","kind":"STATE","label":"Ringförmige Sonnenfinsternis","description":"Zeitpunkt der nächsten ringförmigen Sonnenfinsternis","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#ringElevation","id":"eclipse#ringElevation","channelTypeUID":"astro:elevation","itemType":"Number:Angle","kind":"STATE","label":"Höhenwinkel","description":"Der Höhenwinkel des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#event","id":"eclipse#event","channelTypeUID":"astro:sunEclipseEvent","kind":"TRIGGER","label":"Sonnenfinsternisereignis","description":"Sonnenfinsternisereignis","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:phase#name","id":"phase#name","channelTypeUID":"astro:sunPhaseName","itemType":"String","kind":"STATE","label":"Sonnenphase","description":"Der Name der aktuellen Sonnenphase","defaultTags":[],"properties":{},"configuration":{}}],"label":"Astronomische Sonnendaten","configuration":{"useMeteorologicalSeason":false,"interval":300,"geolocation":"50.65294336725709,8.349609375000002"},"properties":{},"UID":"astro:sun:0a94363608","thingTypeUID":"astro:sun"}',  # noqa: E501
        'type': 'ThingAddedEvent'
    }

    event = get_event(data)
    assert isinstance(event, ThingAddedEvent)
    assert event.name == 'astro:sun:0a94363608'
    assert event.type == 'astro:sun'
    assert event.label == 'Astronomische Sonnendaten'
    assert event.configuration == {
        'useMeteorologicalSeason': False, 'interval': 300, 'geolocation': '50.65294336725709,8.349609375000002'}
    assert event.properties == {}


def test_thing_ThingRemovedEvent():
    data = {
        'topic': 'openhab/things/astro:sun:0a94363608/removed',
        'payload': '{"channels":[{"uid":"astro:sun:0a94363608:rise#start","id":"rise#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:rise#end","id":"rise#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:rise#duration","id":"rise#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:rise#event","id":"rise#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:set#start","id":"set#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:set#end","id":"set#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:set#duration","id":"set#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:set#event","id":"set#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:noon#start","id":"noon#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:noon#end","id":"noon#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:noon#duration","id":"noon#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:noon#event","id":"noon#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:night#start","id":"night#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:night#end","id":"night#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:night#duration","id":"night#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:night#event","id":"night#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:morningNight#start","id":"morningNight#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:morningNight#end","id":"morningNight#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:morningNight#duration","id":"morningNight#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:morningNight#event","id":"morningNight#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDawn#start","id":"astroDawn#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDawn#end","id":"astroDawn#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDawn#duration","id":"astroDawn#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:astroDawn#event","id":"astroDawn#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDawn#start","id":"nauticDawn#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDawn#end","id":"nauticDawn#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDawn#duration","id":"nauticDawn#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:nauticDawn#event","id":"nauticDawn#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDawn#start","id":"civilDawn#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDawn#end","id":"civilDawn#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDawn#duration","id":"civilDawn#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:civilDawn#event","id":"civilDawn#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDusk#start","id":"astroDusk#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDusk#end","id":"astroDusk#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:astroDusk#duration","id":"astroDusk#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:astroDusk#event","id":"astroDusk#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDusk#start","id":"nauticDusk#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDusk#end","id":"nauticDusk#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:nauticDusk#duration","id":"nauticDusk#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:nauticDusk#event","id":"nauticDusk#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDusk#start","id":"civilDusk#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDusk#end","id":"civilDusk#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:civilDusk#duration","id":"civilDusk#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:civilDusk#event","id":"civilDusk#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:eveningNight#start","id":"eveningNight#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:eveningNight#end","id":"eveningNight#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:eveningNight#duration","id":"eveningNight#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eveningNight#event","id":"eveningNight#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:daylight#start","id":"daylight#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:daylight#end","id":"daylight#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:daylight#duration","id":"daylight#duration","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Dauer","description":"Die Dauer des Ereignisses","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:daylight#event","id":"daylight#event","channelTypeUID":"astro:rangeEvent","kind":"TRIGGER","label":"Zeitraum","description":"Zeitraum für ein Ereignis.","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:position#azimuth","id":"position#azimuth","channelTypeUID":"astro:azimuth","itemType":"Number:Angle","kind":"STATE","label":"Azimut","description":"Das Azimut des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:position#elevation","id":"position#elevation","channelTypeUID":"astro:elevation","itemType":"Number:Angle","kind":"STATE","label":"Höhenwinkel","description":"Der Höhenwinkel des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:position#shadeLength","id":"position#shadeLength","channelTypeUID":"astro:shadeLength","itemType":"Number","kind":"STATE","label":"Schattenlängenverhältnis","description":"Projiziertes Schattenlängenverhältnis (Abgeleitet vom Höhenwinkel)","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:radiation#direct","id":"radiation#direct","channelTypeUID":"astro:directRadiation","itemType":"Number:Intensity","kind":"STATE","label":"Direkte Strahlung","description":"Höhe der Strahlung nach Eindringen in die atmosphärische Schicht","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:radiation#diffuse","id":"radiation#diffuse","channelTypeUID":"astro:diffuseRadiation","itemType":"Number:Intensity","kind":"STATE","label":"Diffuse Strahlung","description":"Höhe der Strahlung, nach Beugung durch Wolken und Atmosphäre","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:radiation#total","id":"radiation#total","channelTypeUID":"astro:totalRadiation","itemType":"Number:Intensity","kind":"STATE","label":"Gesamtstrahlung","description":"Gesamtmenge der Strahlung auf dem Boden","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:zodiac#start","id":"zodiac#start","channelTypeUID":"astro:start","itemType":"DateTime","kind":"STATE","label":"Startzeit","description":"Die Startzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:zodiac#end","id":"zodiac#end","channelTypeUID":"astro:end","itemType":"DateTime","kind":"STATE","label":"Endzeit","description":"Die Endzeit des Ereignisses","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:zodiac#sign","id":"zodiac#sign","channelTypeUID":"astro:sign","itemType":"String","kind":"STATE","label":"Sternzeichen","description":"Das Sternzeichen","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#name","id":"season#name","channelTypeUID":"astro:seasonName","itemType":"String","kind":"STATE","label":"Jahreszeit","description":"Der Name der aktuellen Jahreszeit","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#spring","id":"season#spring","channelTypeUID":"astro:spring","itemType":"DateTime","kind":"STATE","label":"Frühling","description":"Frühlingsanfang","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#summer","id":"season#summer","channelTypeUID":"astro:summer","itemType":"DateTime","kind":"STATE","label":"Sommer","description":"Sommeranfang","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#autumn","id":"season#autumn","channelTypeUID":"astro:autumn","itemType":"DateTime","kind":"STATE","label":"Herbst","description":"Herbstanfang","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#winter","id":"season#winter","channelTypeUID":"astro:winter","itemType":"DateTime","kind":"STATE","label":"Winter","description":"Winteranfang","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#nextName","id":"season#nextName","channelTypeUID":"astro:seasonName","itemType":"String","kind":"STATE","label":"Nächste Jahreszeit","description":"Der Name der nächsten Jahreszeit","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:season#timeLeft","id":"season#timeLeft","channelTypeUID":"astro:duration","itemType":"Number:Time","kind":"STATE","label":"Verbleibende Zeit","description":"Die verbleibende Zeit bis zum nächsten Jahreszeitwechsel","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#total","id":"eclipse#total","channelTypeUID":"astro:total","itemType":"DateTime","kind":"STATE","label":"Totale Sonnenfinsternis","description":"Zeitpunkt der nächsten totalen Sonnenfinsternis","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#totalElevation","id":"eclipse#totalElevation","channelTypeUID":"astro:elevation","itemType":"Number:Angle","kind":"STATE","label":"Höhenwinkel","description":"Der Höhenwinkel des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#partial","id":"eclipse#partial","channelTypeUID":"astro:partial","itemType":"DateTime","kind":"STATE","label":"Partielle Sonnenfinsternis","description":"Zeitpunkt der nächsten partiellen Sonnenfinsternis","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#partialElevation","id":"eclipse#partialElevation","channelTypeUID":"astro:elevation","itemType":"Number:Angle","kind":"STATE","label":"Höhenwinkel","description":"Der Höhenwinkel des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#ring","id":"eclipse#ring","channelTypeUID":"astro:ring","itemType":"DateTime","kind":"STATE","label":"Ringförmige Sonnenfinsternis","description":"Zeitpunkt der nächsten ringförmigen Sonnenfinsternis","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#ringElevation","id":"eclipse#ringElevation","channelTypeUID":"astro:elevation","itemType":"Number:Angle","kind":"STATE","label":"Höhenwinkel","description":"Der Höhenwinkel des Himmelskörpers","defaultTags":[],"properties":{},"configuration":{}},{"uid":"astro:sun:0a94363608:eclipse#event","id":"eclipse#event","channelTypeUID":"astro:sunEclipseEvent","kind":"TRIGGER","label":"Sonnenfinsternisereignis","description":"Sonnenfinsternisereignis","defaultTags":[],"properties":{},"configuration":{"offset":0}},{"uid":"astro:sun:0a94363608:phase#name","id":"phase#name","channelTypeUID":"astro:sunPhaseName","itemType":"String","kind":"STATE","label":"Sonnenphase","description":"Der Name der aktuellen Sonnenphase","defaultTags":[],"properties":{},"configuration":{}}],"label":"Astronomische Sonnendaten","configuration":{"useMeteorologicalSeason":false,"interval":300,"geolocation":"50.65294336725709,8.349609375000002"},"properties":{},"UID":"astro:sun:0a94363608","thingTypeUID":"astro:sun"}',  # noqa: E501
        'type': 'ThingRemovedEvent'
    }

    event = get_event(data)
    assert isinstance(event, ThingRemovedEvent)
    assert event.name == 'astro:sun:0a94363608'
    assert event.type == 'astro:sun'
    assert event.label == 'Astronomische Sonnendaten'
    assert event.configuration == {
        'useMeteorologicalSeason': False, 'interval': 300, 'geolocation': '50.65294336725709,8.349609375000002'}
    assert event.properties == {}


@pytest.mark.parametrize('cls', [*EVENT_LIST])
def test_event_has_name(cls):
    # this test ensure that alle events have a name argument
    c = cls('asdf')
    assert c.name == 'asdf'
