import argparse
import asyncio
import concurrent
import random
import sys
import threading
import time

from nether import Application, Service


class ServiceExample(Service):
  def __init__(self, id, application=None) -> None:
    super().__init__(id, description="service example", application=application)

  async def run(self) -> None:
    print(self.id, self.description)


def task(n):
  result = n
  for i in range(0, 1):
    result = result + i
    time.sleep(random.random() * 10)
    print(f"Task-{n} {threading.current_thread()}, count: {result}", file=sys.stderr)
  print(f"Task-{n} {threading.current_thread()}, total: {result}", file=sys.stderr)
  return result


def example0():
  application = Application(None)
  print(application.platform)


async def example1():
  class MyApplication(Application):
    def __init__(self, *services, settings=argparse.Namespace) -> None:
      super().__init__(*services, configuration=settings)

    async def main(self) -> None:
      result = await asyncio.gather(*[self._event_loop.run_in_executor(self._executor, task, i) for i in range(20)])
      print("Result:", sum(result))
      self.stop()

  app = MyApplication(ServiceExample(id=1))
  await app.start()


def example2():
  class ExampleApplication2(Application):
    def __init__(self, settings=None) -> None:
      super().__init__(configuration=settings)
      self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    async def main(self) -> None:
      # tasks = [
      #     self._event_loop.run_in_executor(self.executor, service.run)
      #     for service in self.services.values()
      # ]
      print("ex 2")
      # print(tasks)
      # results = await asyncio.gather(*tasks)

  application = ExampleApplication2(None)
  print(application.platform)


def example3():  # hello world
  class MyApp(Application):
    async def main(self) -> None:
      print("Hello world")

  app = MyApp()
  app.start()


def example4():  # Task
  class MyApp(Application):
    async def main(self) -> None:
      print("Task service running")
      self.TaskService.schedule(self.task1, self.task2, self.task3)

    async def task1(self):
      print("Task 1 started")
      await asyncio.sleep(3)
      print("Task 1 completed")

    async def task2(self):
      print("Task 2 started")
      await asyncio.sleep(3)
      print("Task 2 completed")

  app = MyApp()
  app.start()


def main() -> None:
  example_number = 0 if len(sys.argv) != 2 else int(sys.argv[1])
  match example_number:
    case 0:
      example0()
    case 1:
      asyncio.run(example1())
    case 3:
      example3()
    case 4:
      example4()
    case _:
      example0()


if __name__ == "__main__":
  main()
