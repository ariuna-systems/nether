import asyncio
import math
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def io_heavy():
    print("Blocking I/O started")
    time.sleep(2)
    print("Blocking I/O done")
    return "Result"


def cpu_heavy(n):
    print(f"Calculating factorial({n})")
    return math.factorial(n)


async def main():
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, io_heavy)
        print(f"Got: {result}")

    with ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, cpu_heavy, 50000)
        print(f"Got: {result}")


asyncio.run(main())
