#!/usr/bin/env python3
"""
Example usage of the Short Break Monitor
Demonstrates how to use the short break monitoring functionality
"""

import time
import threading
from datetime import datetime
from short_break_monitor import ShortBreakMonitor

def example_basic_usage():
    """Basic usage example"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Short Break Monitoring")
    print("=" * 60)
    
    # Create monitor with default settings (2-15 minute breaks)
    monitor = ShortBreakMonitor(
        db_path="example_breaks.db",
        min_break_seconds=120,  # 2 minutes
        max_break_seconds=900,  # 15 minutes
        check_interval=1.0,
        enable_lock_detection=True
    )
    
    print(f"Starting monitor...")
    print(f"Break range: {monitor.min_break_seconds}-{monitor.max_break_seconds} seconds")
    print(f"Lock detection: {'Enabled' if monitor.enable_lock_detection else 'Disabled'}")
    
    monitor.start()
    
    # Let it run for a while
    print("Monitoring for 60 seconds... (try being inactive for 2-15 minutes)")
    time.sleep(60)
    
    monitor.stop()
    
    # Show results
    breaks = monitor.get_recent_breaks(hours=1)
    print(f"\nFound {len(breaks)} short breaks:")
    
    for i, break_data in enumerate(breaks, 1):
        print(f"{i}. {break_data['break_start']} to {break_data['break_end']}: "
              f"{break_data['duration_seconds']:.1f}s "
              f"{'(locked)' if break_data['system_locked'] else ''}")
    
    summary = monitor.get_break_summary(hours=1)
    print(f"\nSummary: {summary['total_breaks']} breaks, "
          f"{summary['total_break_time']:.1f}s total time")

def example_custom_settings():
    """Example with custom settings"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Custom Settings")
    print("=" * 60)
    
    # Create monitor with custom settings
    monitor = ShortBreakMonitor(
        db_path="custom_breaks.db",
        min_break_seconds=180,  # 3 minutes
        max_break_seconds=600,  # 10 minutes
        check_interval=2.0,     # Check every 2 seconds
        enable_lock_detection=False  # Disable lock detection
    )
    
    print(f"Custom settings:")
    print(f"• Break range: {monitor.min_break_seconds}-{monitor.max_break_seconds} seconds")
    print(f"• Check interval: {monitor.check_interval} seconds")
    print(f"• Lock detection: {'Enabled' if monitor.enable_lock_detection else 'Disabled'}")
    
    monitor.start()
    
    print("Monitoring for 30 seconds...")
    time.sleep(30)
    
    monitor.stop()
    
    # Export to CSV
    csv_file = "custom_breaks_export.csv"
    monitor.export_to_csv(csv_file, hours=1)
    print(f"Data exported to: {csv_file}")

def example_integration():
    """Example of integrating with other applications"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Integration Example")
    print("=" * 60)
    
    monitor = ShortBreakMonitor(
        db_path="integration_breaks.db",
        min_break_seconds=60,   # 1 minute
        max_break_seconds=300,  # 5 minutes
        check_interval=1.0,
        enable_lock_detection=True
    )
    
    def background_task():
        """Simulate a background task that runs while monitoring"""
        for i in range(10):
            print(f"Background task iteration {i+1}/10")
            time.sleep(6)  # 6 seconds per iteration
    
    print("Starting monitor with background task...")
    monitor.start()
    
    # Run background task
    task_thread = threading.Thread(target=background_task, daemon=True)
    task_thread.start()
    
    # Wait for task to complete
    task_thread.join()
    
    monitor.stop()
    
    # Show results
    breaks = monitor.get_recent_breaks(hours=1)
    print(f"\nDuring background task, found {len(breaks)} short breaks:")
    
    for break_data in breaks:
        print(f"• {break_data['duration_seconds']:.1f}s break "
              f"({break_data['break_start']} to {break_data['break_end']})")

def main():
    """Run all examples"""
    print("SHORT BREAK MONITOR - USAGE EXAMPLES")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_usage()
        example_custom_settings()
        example_integration()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("Check the generated database files for detailed data.")
        
    except KeyboardInterrupt:
        print("\n\nExamples stopped by user.")
    except Exception as e:
        print(f"\nError running examples: {e}")

if __name__ == "__main__":
    main() 