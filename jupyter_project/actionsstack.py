import asyncio
import logging
import sys
import traceback
from typing import Any, Callable, ClassVar, Dict, NoReturn


class ActionsStack:
    """Process long asynchronous task.

    The task result can only be queried once.
    
    Note: The task start immediately => may bring trouble if the user is not careful,
    this assumes 'conda' handle lockers when appropriate.
    """

    __last_index: ClassVar[int] = 0
    logger: ClassVar[logging.Logger] = logging.getLogger("ActionsStack")

    def __init__(self):
        self.__tasks: Dict[int, asyncio.Task] = dict()

    def cancel(self, idx: int) -> NoReturn:
        """Cancel the task `idx`.
        
        Args:
            idx (int): Task index
        """
        ActionsStack.logger.debug("[jupyter_conda] Cancel task {}.".format(idx))
        if idx not in self.__tasks:
            raise ValueError("Task {} does not exists.".format(idx))

        self.__tasks[idx].cancel()

    def get(self, idx: int) -> Any:
        """Get the task `idx` results or None.
        
        Args:
            idx (int): Task index
        
        Returns:
            Any: None if the task is pending else its result

        Raises:
            ValueError: If the task `idx` does not exists.
            asyncio.CancelledError: If the task `idx` was cancelled.
        """
        if idx not in self.__tasks:
            raise ValueError("Task {} does not exists.".format(idx))

        if self.__tasks[idx].done():
            task = self.__tasks.pop(idx)
            return task.result()
        else:
            return None

    def put(self, task: Callable, *args) -> int:
        """Add a asynchronous task into the queue.
        
        Args:
            task (Callable): Asynchronous task
            *args : arguments of the task

        Returns:
            int: Task id
        """
        ActionsStack.__last_index += 1
        idx = ActionsStack.__last_index

        async def execute_task(idx, f, *args) -> Any:
            try:
                ActionsStack.logger.debug(
                    "[jupyter_conda] Will execute task {}.".format(idx)
                )
                result = await f(*args)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                exception_type, _, tb = sys.exc_info()
                result = {
                    "type": exception_type.__qualname__,
                    "error": str(e),
                    "message": repr(e),
                    "traceback": traceback.format_tb(tb),
                }
                ActionsStack.logger.error(
                    "[jupyter_conda] Error for task {}.".format(result)
                )
            else:
                ActionsStack.logger.debug(
                    "[jupyter_conda] Has executed task {}.".format(idx)
                )

            return result

        self.__tasks[idx] = asyncio.ensure_future(execute_task(idx, task, *args))
        return idx

    def __del__(self):
        for task in filter(lambda t: not t.cancelled(), self.__tasks.values()):
            task.cancel()
