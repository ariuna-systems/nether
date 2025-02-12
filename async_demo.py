import asyncio
import inspect


# Removed in Python 3.10
# @asyncio.coroutine
def custom_coroutine():
    yield from asyncio.sleep(1)


async def demo_0():
    await asyncio.sleep(5)
    print("Demo 0 finished")


async def demo_1():
    async def coroutine():
        print("+++")
        await asyncio.sleep(10)
        print("---")  # should be not printed

    task = asyncio.create_task(coroutine())
    await asyncio.sleep(1)

    cancel_requested = task.cancel()
    await asyncio.sleep(1)
    print(f"Task should be canceled: {cancel_requested}")

    await asyncio.sleep(1)
    print(f"Task already canceled: {task.cancelled()}")

    print("Demo finished")


async def demo_2():
    async def coroutine(number):
        print(f"Task {number} started")
        await asyncio.sleep(10)
        print("---")  # should be not printed

    task_1 = asyncio.create_task(coroutine(1))
    task_2 = asyncio.create_task(coroutine(1))

    await asyncio.sleep(1)
    # cancel_requested = task.cancel()
    await asyncio.sleep(1)
    # print(f"Task should be canceled: {cancel_requested}")

    # await asyncio.sleep(1)
    # print(f"Task already canceled: {task.cancelled()}")

    print("Demo finished")


if __name__ == "__main__":
    print(type(demo_0), asyncio.iscoroutine(demo_0))
    print(type(demo_0), inspect.iscoroutine(demo_0))
    print(type(demo_0), inspect.iscoroutinefunction(demo_0))

    print(type(custom_coroutine), asyncio.iscoroutine(custom_coroutine))
    print(type(custom_coroutine), inspect.iscoroutine(custom_coroutine))

    # asyncio.run(demo_0())
    # asyncio.run(demo_2())

    # RuntimeWarning: coroutine 'demo_0' was never awaited
    # RuntimeWarning: Enable tracemalloc to get the object allocation traceback
    demo_0()

    # OK: Přiřadíme korutinu do proměnné a pak pustíme
    coro = demo_0()
    asyncio.run(coro)

    sleeper = asyncio.sleep(3)
    asyncio.run(sleeper)
