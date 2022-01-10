import asyncio
import logging
import traceback
import typing
from typing import Any, Optional

import aiohttp
from aiohttp.client import ClientResponse, _RequestContextManager
from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT, METH_DELETE
from aiohttp_sse_client import client as sse_client

import HABApp
import HABApp.core
import HABApp.openhab.events
from HABApp.core.const.json import dump_json, load_json
from HABApp.openhab.errors import OpenhabConnectionNotSetUpError, OpenhabNotReadyYet, \
    OpenhabDisconnectedError, ExpectedSuccessFromOpenhab
from .http_connection_waiter import WaitBetweenConnects

log = logging.getLogger('HABApp.openhab.connection')
log_events = logging.getLogger('HABApp.EventBus.openhab')


IS_ONLINE: bool = False
IS_READ_ONLY: bool = False
IS_NOT_SET_UP: bool = True

IS_OH2 = False

# HTTP options
HTTP_ALLOW_REDIRECTS: bool = True
HTTP_VERIFY_SSL: Optional[bool] = None
HTTP_SESSION: aiohttp.ClientSession = None

CONNECT_WAIT: WaitBetweenConnects = WaitBetweenConnects()


FUT_UUID: Optional[asyncio.Future] = None
FUT_SSE: Optional[asyncio.Future] = None


ON_CONNECTED: typing.Callable = None
ON_DISCONNECTED: typing.Callable = None


async def get(url: str, log_404=True, disconnect_on_error=False, **kwargs: Any) -> ClientResponse:
    if IS_NOT_SET_UP:
        raise OpenhabConnectionNotSetUpError()

    mgr = _RequestContextManager(
        HTTP_SESSION._request(METH_GET, url, allow_redirects=HTTP_ALLOW_REDIRECTS, ssl=HTTP_VERIFY_SSL, **kwargs)
    )
    return await check_response(mgr, log_404=log_404, disconnect_on_error=disconnect_on_error)


async def post(url: str, log_404=True, json=None, data=None, **kwargs: Any) -> Optional[ClientResponse]:
    if IS_NOT_SET_UP:
        raise OpenhabConnectionNotSetUpError()

    if IS_READ_ONLY or not IS_ONLINE:
        return None

    # todo: remove this workaround once there is a fix in aiohttp
    headers = None
    if data is not None:
        headers = {'Content-Type': 'text/plain; charset=utf-8'}

    mgr = _RequestContextManager(
        HTTP_SESSION._request(
            METH_POST, url, allow_redirects=HTTP_ALLOW_REDIRECTS, ssl=HTTP_VERIFY_SSL,
            headers=headers, data=data, json=json, **kwargs
        )
    )

    if data is None:
        data = json
    return await check_response(mgr, log_404=log_404, sent_data=data)


async def put(url: str, log_404=True, json=None, data=None, **kwargs: Any) -> Optional[ClientResponse]:
    if IS_NOT_SET_UP:
        raise OpenhabConnectionNotSetUpError()

    if IS_READ_ONLY or not IS_ONLINE:
        return None

    # todo: remove this workaround once there is a fix in aiohttp
    headers = None
    if data is not None:
        headers = {'Content-Type': 'text/plain; charset=utf-8'}

    mgr = _RequestContextManager(
        HTTP_SESSION._request(
            METH_PUT, url, allow_redirects=HTTP_ALLOW_REDIRECTS, ssl=HTTP_VERIFY_SSL,
            headers=headers, data=data, json=json, **kwargs
        )
    )

    if data is None:
        data = json
    return await check_response(mgr, log_404=log_404, sent_data=data)


async def delete(url: str, log_404=True, json=None, data=None, **kwargs: Any) -> Optional[ClientResponse]:
    if IS_NOT_SET_UP:
        raise OpenhabConnectionNotSetUpError()

    if IS_READ_ONLY or not IS_ONLINE:
        return None

    mgr = _RequestContextManager(
        HTTP_SESSION._request(METH_DELETE, url, allow_redirects=HTTP_ALLOW_REDIRECTS, ssl=HTTP_VERIFY_SSL,
                              data=data, json=json, **kwargs)
    )

    if data is None:
        data = json
    return await check_response(mgr, log_404=log_404, sent_data=data)


def set_offline(log_msg=''):
    global IS_ONLINE, FUT_UUID, FUT_SSE

    if not IS_ONLINE:
        return None
    IS_ONLINE = False

    log.warning(f'Disconnected! {log_msg}')

    # cancel SSE listener
    if FUT_SSE is not None:
        if not FUT_SSE.done():
            FUT_SSE.cancel()
        FUT_SSE = None

    ON_DISCONNECTED()

    # Try reconnect
    if not FUT_UUID.done():
        FUT_UUID.cancel()
    FUT_UUID = asyncio.run_coroutine_threadsafe(try_uuid(), HABApp.core.const.loop)


def is_disconnect_exception(e) -> bool:
    if not isinstance(e, (
            # aiohttp Exceptions
            aiohttp.ClientPayloadError, aiohttp.ClientConnectorError, aiohttp.ClientOSError,

            # aiohttp_sse_client Exceptions
            ConnectionRefusedError, ConnectionError, ConnectionAbortedError)):
        return False

    set_offline(str(e))
    return True


async def check_response(future: aiohttp.client._RequestContextManager, sent_data=None,
                         log_404=True, disconnect_on_error=False) -> ClientResponse:
    try:
        resp = await future
    except Exception as e:
        is_disconnect = is_disconnect_exception(e)
        log.log(logging.WARNING if is_disconnect else logging.ERROR, f'"{e}" ({type(e)})')
        if is_disconnect:
            raise OpenhabDisconnectedError()
        raise

    status = resp.status

    # Server Errors if openHAB is not ready yet
    if status >= 500:
        set_offline(f'Status {status} for {resp.request_info.method} {resp.request_info.url}')
        raise OpenhabNotReadyYet()

    # Sometimes openHAB issues 404 instead of 500 during startup
    if disconnect_on_error and status >= 400:
        set_offline(f'Expected success but got status {status} for '
                    f'{str(resp.request_info.url).replace(HABApp.CONFIG.openhab.connection.url, "")}')
        raise ExpectedSuccessFromOpenhab()

    # Something went wrong - log error message
    log_msg = False
    if status >= 300:
        log_msg = True

        # possibility skip logging of 404
        if status == 404 and not log_404:
            log_msg = False

    if log_msg:
        # Log Error Message
        sent = '' if sent_data is None else f' {sent_data}'
        log.warning(f'Status {status} for {resp.request_info.method} {resp.request_info.url}{sent}')
        for line in str(resp).splitlines():
            log.debug(line)

    return resp


async def stop_connection():
    global FUT_UUID, FUT_SSE, HTTP_SESSION
    if FUT_UUID is not None and not FUT_UUID.done():
        FUT_UUID.cancel()
        FUT_UUID = None

    if FUT_SSE is not None and not FUT_SSE.done():
        FUT_SSE.cancel()
        FUT_SSE = None

    await asyncio.sleep(0)

    # If we are already connected properly disconnect
    if HTTP_SESSION is not None:
        await HTTP_SESSION.close()
        HTTP_SESSION = None


async def start_connection():
    global HTTP_SESSION, FUT_UUID, IS_NOT_SET_UP, HTTP_VERIFY_SSL

    await stop_connection()

    url: str = HABApp.CONFIG.openhab.connection.url

    # do not run without an url
    if url == '':
        IS_NOT_SET_UP = True
        return None
    IS_NOT_SET_UP = False

    auth = None
    if HABApp.CONFIG.openhab.connection.user or HABApp.CONFIG.openhab.connection.password:
        auth = aiohttp.BasicAuth(
            HABApp.CONFIG.openhab.connection.user,
            HABApp.CONFIG.openhab.connection.password
        )

    if not HABApp.CONFIG.openhab.connection.verify_ssl:
        HTTP_VERIFY_SSL = False
        log.info('Verify ssl set to False!')
    else:
        HTTP_VERIFY_SSL = None

    # todo: add possibility to configure line size with read_bufsize
    HTTP_SESSION = aiohttp.ClientSession(
        base_url=url,
        timeout=aiohttp.ClientTimeout(total=None),
        json_serialize=dump_json,
        auth=auth,
        read_bufsize=2**19  # 512k buffer,
    )

    FUT_UUID = asyncio.create_task(try_uuid())


async def start_sse_event_listener():
    try:
        # cache so we don't have to look up every event
        _load_json = load_json
        _see_handler = on_sse_event

        event_prefix = 'openhab' if not IS_OH2 else 'smarthome'

        async with sse_client.EventSource(
                url=f'/rest/events?topics='
                    f'{event_prefix}/items/,'                   # Item updates
                    f'{event_prefix}/channels/,'                # Channel update
                    f'{event_prefix}/things/*/status,'          # Thing status updates
                    f'{event_prefix}/things/*/statuschanged'    # Thing status changes
                ,
                session=HTTP_SESSION,
                ssl=None if HABApp.CONFIG.openhab.connection.verify_ssl else False
        ) as event_source:
            async for event in event_source:

                e_str = event.data

                try:
                    e_json = _load_json(e_str)
                except ValueError:
                    log_events.warning(f'Invalid json: {e_str}')
                    continue
                except TypeError:
                    log_events.warning(f'Invalid json: {e_str}')
                    continue

                # Log sse event
                if log_events.isEnabledFor(logging.DEBUG):
                    log_events._log(logging.DEBUG, e_str, [])

                # process
                _see_handler(e_json)

    except asyncio.CancelledError:
        # This exception gets raised if we cancel the coroutine
        # since this is normal behaviour we ignore this exception
        pass
    except Exception as e:
        disconnect = is_disconnect_exception(e)
        lvl = logging.WARNING if disconnect else logging.ERROR
        log.log(lvl, f'SSE request Error: {e}')
        for line in traceback.format_exc().splitlines():
            log.log(lvl, line)

        # reconnect even if we have an unexpected error
        if not disconnect:
            set_offline(f'Uncaught error in process_sse_events: {e}')


async def async_get_uuid() -> str:
    resp = await get('/rest/uuid', log_404=False)
    if resp.status >= 300:
        raise OpenhabNotReadyYet()
    return await resp.text(encoding='utf-8')


async def async_get_root() -> dict:
    resp = await get('/rest/', log_404=False)
    if resp.status == 404:
        return {}
    return await resp.json(loads=load_json, encoding='utf-8')


def patch_for_oh2(reverse=False):
    global IS_OH2

    IS_OH2 = True

    # events are named different
    HABApp.openhab.events.item_events.NAME_START = 16 if not reverse else 14
    HABApp.openhab.events.thing_events.NAME_START = 17 if not reverse else 15
    HABApp.openhab.events.channel_events.NAME_START = 19 if not reverse else 17


async def try_uuid():
    global FUT_UUID, FUT_SSE, IS_ONLINE

    # sleep before reconnect
    await CONNECT_WAIT.wait()

    log.debug('Trying to connect to OpenHAB ...')
    try:
        uuid = await async_get_uuid()
        root = await async_get_root()      # this will only work on OH3
    except Exception as e:
        if isinstance(e, (OpenhabDisconnectedError, OpenhabNotReadyYet, ExpectedSuccessFromOpenhab)):
            log.info('... offline!')
        else:
            for line in traceback.format_exc().splitlines():
                log.error(line)

        # Keep trying to connect
        FUT_UUID = asyncio.create_task(try_uuid())
        return None

    if IS_READ_ONLY:
        log.info(f'Connected read only to OpenHAB instance {uuid}')
    else:
        log.info(f'Connected to OpenHAB instance {uuid}')

    info = root.get('runtimeInfo')
    if info is None:
        patch_for_oh2()
    else:
        log.info(f'OpenHAB version {info["version"]} ({info["buildString"]})')

    IS_ONLINE = True

    # start sse processing
    if FUT_SSE is not None:
        FUT_SSE.cancel()
    FUT_SSE = asyncio.create_task(start_sse_event_listener())

    ON_CONNECTED()
    return None


def __load_cfg():
    global IS_READ_ONLY
    IS_READ_ONLY = HABApp.config.CONFIG.openhab.general.listen_only


# setup config
__load_cfg()
HABApp.config.CONFIG.subscribe_for_changes(__load_cfg)


# import it here otherwise we get cyclic imports
from HABApp.openhab.connection_handler.sse_handler import on_sse_event  # noqa: E402
