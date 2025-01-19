from functools import wraps
from pydispatch import dispatcher
import yappi
from datetime import datetime


def profile_with_yappi(
  output_file='node_controller_init_profile.txt',  # Changed extension to .txt
  signal='on_component_ready',
):
  """
  Decorator that profiles a function's performance with human-readable timing information.
  """

  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      # Record start time
      start_time = datetime.utcnow()
      # Configure yappi to track wall clock time
      yappi.set_clock_type('wall')  # Use wall clock time for more intuitive results
      yappi.start()

      def stop_yappi(sender):
        end_time = datetime.utcnow()
        yappi.stop()

        # Get the stats
        stats = yappi.get_func_stats()

        # Write human-readable output
        with open(output_file, 'w') as f:
          f.write('Profile Results\n')
          f.write('==============\n')
          f.write(f'Start Time (UTC): {start_time}\n')
          f.write(f'End Time (UTC): {end_time}\n')
          f.write(f'Total Duration: {end_time - start_time}\n\n')
          f.write('Function Timing Details:\n')
          f.write('----------------------\n')

          # Sort stats by total time spent
          stats.sort('ttot')  # Sort by total time

          # Write function statistics in a readable format
          for stat in stats:
            f.write(f'\nFunction: {stat.name}\n')
            f.write(f'  Module: {stat.module}\n')
            f.write(f'  Number of calls: {stat.ncall}\n')
            f.write(f'  Total time: {stat.ttot:.3f} seconds\n')
            f.write(f'  Time per call: {stat.tavg:.3f} seconds\n')

        # Also save callgrind format for tools like KCachegrind
        stats.save(f'{output_file}.callgrind', type='callgrind')

        if signal in dispatcher.getAllReceivers():
          dispatcher.disconnect(stop_yappi, signal=signal)

      dispatcher.connect(stop_yappi, signal=signal)
      try:
        result = func(*args, **kwargs)
        return result
      finally:
        stop_yappi(None)

    return wrapper

  return decorator
