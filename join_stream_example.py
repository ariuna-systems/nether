#!/usr/bin/env python3
"""
Example demonstrating join_stream usage in nether framework
Scenario: Real-time sensor data processing with multiple processors
"""

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import random
import time

# Add src to path to import nether
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nether.component import Component
from nether.message import Command, Event
from nether.application import Nether


@dataclass(frozen=True, kw_only=True, slots=True)
class StartDataCollection(Command):
  duration_seconds: int = 10


@dataclass(frozen=True, kw_only=True, slots=True)
class StopDataCollection(Command):
  pass


@dataclass(frozen=True, kw_only=True, slots=True)
class DataProcessed(Event):
  processor_name: str
  processed_count: int


class SensorDataProducer(Component[StartDataCollection | StopDataCollection]):
  """Produces streaming sensor data to the shared stream"""

  def __init__(self, application):
    super().__init__(application)
    self._producing = False

  async def handle(self, message, *, dispatch, join_stream):
    match message:
      case StartDataCollection():
        await self._start_producing(message, dispatch, join_stream)
      case StopDataCollection():
        self._producing = False
        # Signal all consumers to stop
        stream_queue, stop_event = join_stream()
        stop_event.set()
        print("🛑 Producer: Stopping data collection")

  async def _start_producing(self, command, dispatch, join_stream):
    """Produce sensor data to the shared stream"""
    stream_queue, stop_event = join_stream()
    self._producing = True

    print(f"🔄 Producer: Starting data collection for {command.duration_seconds} seconds")

    start_time = time.time()
    data_count = 0

    while self._producing and not stop_event.is_set():
      # Simulate sensor readings
      sensor_data = {
        "timestamp": time.time(),
        "temperature": round(random.uniform(20.0, 30.0), 2),
        "humidity": round(random.uniform(40.0, 80.0), 2),
        "pressure": round(random.uniform(1000.0, 1020.0), 2),
        "data_id": data_count,
      }

      # Put data into the shared stream
      await stream_queue.put(sensor_data)
      data_count += 1

      print(f"📊 Producer: Generated data #{data_count} - Temp: {sensor_data['temperature']}°C")

      # Check if duration exceeded
      if time.time() - start_time >= command.duration_seconds:
        await dispatch(StopDataCollection())
        break

      await asyncio.sleep(0.5)  # Produce data every 500ms


class TemperatureProcessor(Component[StartDataCollection]):
  """Processes temperature data from the stream"""

  def __init__(self, application):
    super().__init__(application)
    self.processed_count = 0

  async def handle(self, message, *, dispatch, join_stream):
    """Start consuming temperature data from the stream"""
    stream_queue, stop_event = join_stream()

    print("🌡️  Temperature Processor: Started monitoring")

    while not stop_event.is_set():
      try:
        # Wait for data with timeout
        data = await asyncio.wait_for(stream_queue.get(), timeout=1.0)

        # Process temperature-specific logic
        temp = data.get("temperature", 0)
        if temp > 25.0:
          print(f"🔥 Temperature Alert: {temp}°C is high! (Data #{data['data_id']})")
        elif temp < 22.0:
          print(f"🧊 Temperature Alert: {temp}°C is low! (Data #{data['data_id']})")

        self.processed_count += 1

        # Report progress every 5 readings
        if self.processed_count % 5 == 0:
          await dispatch(DataProcessed(processor_name="TemperatureProcessor", processed_count=self.processed_count))

      except asyncio.TimeoutError:
        continue  # Keep waiting for data

    print(f"🌡️  Temperature Processor: Stopped. Processed {self.processed_count} readings")


class HumidityProcessor(Component[StartDataCollection]):
  """Processes humidity data from the same stream"""

  def __init__(self, application):
    super().__init__(application)
    self.processed_count = 0

  async def handle(self, message, *, dispatch, join_stream):
    """Start consuming humidity data from the stream"""
    stream_queue, stop_event = join_stream()

    print("💧 Humidity Processor: Started monitoring")

    while not stop_event.is_set():
      try:
        # Wait for data with timeout
        data = await asyncio.wait_for(stream_queue.get(), timeout=1.0)

        # Process humidity-specific logic
        humidity = data.get("humidity", 0)
        if humidity > 70.0:
          print(f"💦 Humidity Alert: {humidity}% is very humid! (Data #{data['data_id']})")
        elif humidity < 50.0:
          print(f"🏜️  Humidity Alert: {humidity}% is dry! (Data #{data['data_id']})")

        self.processed_count += 1

        # Report progress every 3 readings
        if self.processed_count % 3 == 0:
          await dispatch(DataProcessed(processor_name="HumidityProcessor", processed_count=self.processed_count))

      except asyncio.TimeoutError:
        continue

    print(f"💧 Humidity Processor: Stopped. Processed {self.processed_count} readings")


class DataAggregator(Component[StartDataCollection]):
  """Aggregates statistics from the stream"""

  def __init__(self, application):
    super().__init__(application)
    self.readings = []

  async def handle(self, message, *, dispatch, join_stream):
    """Collect all data for statistical analysis"""
    stream_queue, stop_event = join_stream()

    print("📈 Data Aggregator: Started collecting statistics")

    while not stop_event.is_set():
      try:
        data = await asyncio.wait_for(stream_queue.get(), timeout=1.0)
        self.readings.append(data)

        # Print running statistics every 10 readings
        if len(self.readings) % 10 == 0:
          avg_temp = sum(r["temperature"] for r in self.readings) / len(self.readings)
          avg_humidity = sum(r["humidity"] for r in self.readings) / len(self.readings)
          print(
            f"📊 Stats: {len(self.readings)} readings - Avg Temp: {avg_temp:.1f}°C, Avg Humidity: {avg_humidity:.1f}%"
          )

      except asyncio.TimeoutError:
        continue

    # Final statistics
    if self.readings:
      avg_temp = sum(r["temperature"] for r in self.readings) / len(self.readings)
      avg_humidity = sum(r["humidity"] for r in self.readings) / len(self.readings)
      max_temp = max(r["temperature"] for r in self.readings)
      min_temp = min(r["temperature"] for r in self.readings)

      print(f"📈 Final Statistics:")
      print(f"   Total readings: {len(self.readings)}")
      print(f"   Average temperature: {avg_temp:.1f}°C")
      print(f"   Temperature range: {min_temp:.1f}°C - {max_temp:.1f}°C")
      print(f"   Average humidity: {avg_humidity:.1f}%")


class ProgressReporter(Component[DataProcessed]):
  """Reports processing progress from different processors"""

  def __init__(self, application):
    super().__init__(application)

  async def handle(self, message, *, dispatch, join_stream):
    print(f"📋 Progress: {message.processor_name} has processed {message.processed_count} items")


class SensorApp(Nether):
  async def main(self):
    print("🚀 Sensor Data Processing System Started")
    print("This demonstrates join_stream for coordinating multiple processors on shared data")

    # Start data collection for 8 seconds
    async with self.mediator.context() as ctx:
      await ctx.process(StartDataCollection(duration_seconds=8))


async def main():
  import argparse

  config = argparse.Namespace()
  app = SensorApp(configuration=config)

  # Attach all components
  app.attach(SensorDataProducer(app))
  app.attach(TemperatureProcessor(app))
  app.attach(HumidityProcessor(app))
  app.attach(DataAggregator(app))
  app.attach(ProgressReporter(app))

  await app.start()


if __name__ == "__main__":
  print("=" * 60)
  print("JOIN_STREAM EXAMPLE: Real-time Sensor Data Processing")
  print("=" * 60)
  print()

  asyncio.run(main())
