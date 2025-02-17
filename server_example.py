import argparse
import asyncio

from arjuna.nether import Application
from arjuna.nether.server import HTTPInterfaceService


class MyApplication(Application):
  async def main(self) -> None:
    print("Hello, world!")


async def main():
  configuration = argparse.Namespace()
  configuration.host = "localhost"
  configuration.port = 8080
  app = MyApplication(configuration=configuration)
  server = HTTPInterfaceService(configuration=configuration)
  app.register_service(server)
  await app.start()


if __name__ == "__main__":
  asyncio.run(main())
