"""UI utility functions"""

from abc import abstractmethod
import asyncio
from collections.abc import Coroutine


def valid_int(i_str: str):
    """Check if a int value is valid"""
    try:
        float(i_str)
    except:
        return False
    else:
        return True

def valid_float(f_str: str):
    """Check if a float value is valid"""
    try:
        float(f_str)
    except:
        return False
    else:
        return True
    
def make_task(coroutine: Coroutine,
              task_set: set[asyncio.Task] | None = None,
              loop: asyncio.AbstractEventLoop | None = None
              )-> tuple[asyncio.Task, set[asyncio.Task] | None]:
    """Make a task and assign it to the given loop.
    
    Args:
        coroutine: awaitable coroutine
        task_set: set keeping track of tasks
        loop: event loop to use, if None, use 'asyncio' default
    Returns:
        task: task which was created
        task_set: modified task set
    """
    if not loop:
        loop = asyncio.get_event_loop()
    t = loop.create_task(coroutine)
    if task_set:
        t.add_done_callback(task_set.discard)
        task_set.add(t)
    return t, task_set

class Cyclic:
    """Cyclic Task Mixin"""

    @abstractmethod
    async def update(self):
        pass

    async def update_loop(self, interval: float = 1/60):
        """Update self in a loop
                
        interval: time in seconds between updates
        """
        while True:
            await asyncio.gather(self.update(), asyncio.sleep(interval))

    @abstractmethod
    def close(self):
        pass