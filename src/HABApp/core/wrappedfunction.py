import io
import logging
import time
from asyncio import iscoroutinefunction
from cProfile import Profile
from concurrent.futures import ThreadPoolExecutor
from pstats import SortKey
from pstats import Stats
from typing import Optional
from HABApp.core.base import WrappedFunctionBase

import HABApp
from HABApp.core.asyncio import async_context, create_task

default_logger = logging.getLogger('HABApp.Worker')


class WrappedFunction(WrappedFunctionBase):
    _WORKERS = ThreadPoolExecutor(10, 'HabApp_')

    def __init__(self, func, logger=None, warn_too_long=True, name: Optional[str] = None,
                 rule_ctx: Optional['HABApp.rule_ctx.HABAppRuleContext'] = None):

        # Allow setting of the rule context
        self._habapp_rule_ctx = rule_ctx

        assert callable(func)
        self._func = func

        # name of the function
        if name is None:
            if rule_ctx is not None:
                name = rule_ctx.get_callback_name(func)
            else:
                name = self._func.__name__
        self.name = name

        self.is_async = iscoroutinefunction(self._func)

        self.__time_submitted = 0.0

        # Allow custom logger
        self.log = default_logger
        if logger:
            self.log = logger

        self.__warn_too_long = warn_too_long

    def run(self, *args, **kwargs):

        if self.is_async:
            create_task(self.async_run(*args, **kwargs))
        else:
            self.__time_submitted = time.time()
            WrappedFunction._WORKERS.submit(self.__run, *args, **kwargs)

    def __format_traceback(self, e: Exception, *args, **kwargs):

        lines = HABApp.core.wrapper.format_exception(e)

        # Log Exception
        self.log.error(f'Error in {self.name}: {e}')
        for line in lines:
            self.log.error(line)

        # create HABApp event, but only if we are not currently processing one
        if not args or not isinstance(args[0], HABApp.core.events.habapp_events.HABAppException):
            HABApp.core.EventBus.post_event(
                HABApp.core.const.topics.ERRORS, HABApp.core.events.habapp_events.HABAppException(
                    func_name=self.name, exception=e, traceback='\n'.join(lines)
                )
            )

    async def async_run(self, *args, **kwargs):

        token = async_context.set('WrappedFunction')

        try:
            await self._func(*args, **kwargs)
        except Exception as e:
            self.__format_traceback(e, *args, **kwargs)

        async_context.reset(token)
        return None

    def __run(self, *args, **kwargs):
        __start = time.time()

        # notify if we don't process quickly
        if __start - self.__time_submitted > 0.05:
            self.log.warning(f'Starting of {self.name} took too long: {__start - self.__time_submitted:.2f}s. '
                             f'Maybe there are not enough threads?')

        # start profiler
        pr = Profile()
        pr.enable()

        # Execute the function
        try:
            self._func(*args, **kwargs)
        except Exception as e:
            self.__format_traceback(e, *args, **kwargs)

        # disable profiler
        pr.disable()

        # log warning if execution takes too long
        __dur = time.time() - __start
        if self.__warn_too_long and __dur > 0.8:
            self.log.warning(f'Execution of {self.name} took too long: {__dur:.2f}s')

            s = io.StringIO()
            ps = Stats(pr, stream=s).sort_stats(SortKey.CUMULATIVE)
            ps.print_stats(0.1)  # limit to output to 10% of the lines

            for line in s.getvalue().splitlines()[4:]:    # skip the amount of calls and "Ordered by:"
                if line:
                    self.log.warning(line)
