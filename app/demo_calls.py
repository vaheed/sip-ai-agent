#!/usr/bin/env python3
"""
Demo script to simulate calls for testing the web dashboard.

This script creates simulated call data to demonstrate the web UI functionality
including call history, statistics, and real-time updates.
"""

import asyncio
import random
import time
from datetime import datetime, timedelta

from call_history import get_call_history_manager
from logging_config import get_logger

logger = get_logger("demo_calls")


class CallSimulator:
    """Simulates SIP calls for demo purposes."""

    def __init__(self):
        self.call_history_manager = get_call_history_manager()
        self.running = False
        self.simulated_calls = []

    async def create_demo_calls(self, count: int = 10):
        """Create demo calls with realistic data."""
        logger.info("Creating demo calls", count=count)

        # Create some historical calls
        for i in range(count):
            call_id = f"demo-call-{i+1:03d}"

            # Random caller/callee numbers
            caller_num = random.randint(1000, 9999)  # nosec B311
            callee_num = random.randint(1000, 9999)  # nosec B311
            caller = f"+1555{caller_num}"
            callee = f"+1555{callee_num}"

            # Random start time in the last 7 days
            start_time = time.time() - random.randint(0, 7 * 24 * 3600)  # nosec B311

            # Create call item
            call_item = self.call_history_manager.start_call(
                call_id=call_id, caller=caller, callee=callee, direction="incoming"
            )

            # Set start time manually for demo
            call_item.start_time = start_time

            # Random duration (30 seconds to 10 minutes)
            duration = random.randint(30, 600)  # nosec B311
            end_time = start_time + duration

            # Random token usage
            tokens_used = random.randint(100, 2000)  # nosec B311
            call_item.update_tokens(tokens_used)

            # Random cost calculation (rough estimate)
            call_item.cost = tokens_used * 0.0001

            # Random audio quality metrics
            call_item.update_audio_quality(
                {
                    "packet_loss": random.uniform(0, 0.05),  # nosec B311
                    "jitter": random.uniform(0, 50),  # nosec B311
                    "latency": random.uniform(50, 200),  # nosec B311
                    "mos_score": random.uniform(3.0, 5.0),  # nosec B311
                }
            )

            # End the call
            status = random.choice(
                ["completed", "completed", "completed", "failed"]
            )  # nosec B311
            error_message = "Network timeout" if status == "failed" else None

            call_item.end_call(status, error_message)
            call_item.end_time = end_time
            call_item.duration = duration

            self.simulated_calls.append(call_item)

            logger.info(
                "Demo call created",
                call_id=call_id,
                duration=duration,
                tokens=tokens_used,
                status=status,
            )

    async def simulate_live_calls(self, duration_minutes: int = 5):
        """Simulate live calls for demo purposes."""
        logger.info("Starting live call simulation", duration_minutes=duration_minutes)
        self.running = True

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        call_counter = 1

        while self.running and time.time() < end_time:
            # Random interval between calls (10-60 seconds)
            sleep_time = random.randint(10, 60)  # nosec B311
            await asyncio.sleep(sleep_time)

            call_id = f"live-call-{call_counter:03d}"
            caller_num = random.randint(1000, 9999)  # nosec B311
            callee_num = random.randint(1000, 9999)  # nosec B311
            caller = f"+1555{caller_num}"
            callee = f"+1555{callee_num}"

            # Start call
            call_item = self.call_history_manager.start_call(
                call_id=call_id, caller=caller, callee=callee, direction="incoming"
            )

            logger.info("Live call started", call_id=call_id, caller=caller)

            # Simulate call duration (30 seconds to 5 minutes)
            call_duration = random.randint(30, 300)  # nosec B311
            await asyncio.sleep(call_duration)

            # Update tokens during call
            tokens_used = random.randint(200, 1500)  # nosec B311
            call_item.update_tokens(tokens_used)

            # Update audio quality
            call_item.update_audio_quality(
                {
                    "packet_loss": random.uniform(0, 0.02),  # nosec B311
                    "jitter": random.uniform(0, 30),  # nosec B311
                    "latency": random.uniform(50, 150),  # nosec B311
                    "mos_score": random.uniform(4.0, 5.0),  # nosec B311
                }
            )

            # End call
            status = random.choice(
                ["completed", "completed", "completed", "failed"]
            )  # nosec B311
            error_message = "Call dropped" if status == "failed" else None

            call_item.end_call(status, error_message)

            logger.info(
                "Live call ended",
                call_id=call_id,
                duration=call_duration,
                tokens=tokens_used,
                status=status,
            )

            call_counter += 1

    def stop_simulation(self):
        """Stop the live call simulation."""
        self.running = False
        logger.info("Live call simulation stopped")

    def get_statistics(self):
        """Get call statistics."""
        return self.call_history_manager.get_call_statistics()

    def clear_demo_data(self):
        """Clear all demo data."""
        self.call_history_manager.call_history.clear()
        self.call_history_manager.active_calls.clear()
        self.simulated_calls.clear()
        logger.info("Demo data cleared")


async def main():
    """Main demo function."""
    simulator = CallSimulator()

    print("SIP AI Agent - Call Simulation Demo")
    print("=" * 40)

    # Create historical demo calls
    print("Creating historical demo calls...")
    await simulator.create_demo_calls(15)

    # Show statistics
    stats = simulator.get_statistics()
    print("\nCall Statistics:")
    print(f"  Total calls: {stats['total_calls']}")
    print(f"  Completed: {stats['completed_calls']}")
    print(f"  Failed: {stats['failed_calls']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Average duration: {stats['average_duration']:.1f}s")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Total cost: ${stats['total_cost']:.4f}")

    # Start live simulation
    print("\nStarting live call simulation (5 minutes)...")
    print("Press Ctrl+C to stop")

    try:
        await simulator.simulate_live_calls(5)
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
        simulator.stop_simulation()

    # Final statistics
    final_stats = simulator.get_statistics()
    print("\nFinal Statistics:")
    print(f"  Total calls: {final_stats['total_calls']}")
    print(f"  Completed: {final_stats['completed_calls']}")
    print(f"  Failed: {final_stats['failed_calls']}")
    print(f"  Success rate: {final_stats['success_rate']:.1%}")
    print(f"  Average duration: {final_stats['average_duration']:.1f}s")
    print(f"  Total tokens: {final_stats['total_tokens']}")
    print(f"  Total cost: ${final_stats['total_cost']:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
