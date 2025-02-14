import logging


def init_signal_handlers(instance) -> None:
  """
  Initialize all signal handlers for an instance.
  Call this after event_bus is set.
  """
  if not hasattr(instance, 'event_bus'):
    logging.warning(f'{instance.__class__.__name__} has no event_bus attribute')
    return

  # Find all methods decorated with @handle_signal
  for attr_name in dir(instance):
    attr = getattr(instance, attr_name)
    if hasattr(attr, '_is_signal_handler') and attr._is_signal_handler:
      try:
        signal_type = attr._signal_type
        instance.event_bus.subscribe(signal_type, attr)
        logging.debug(
          f'Subscribed {instance.__class__.__name__}.{attr_name} to {signal_type.name}'
        )
      except Exception as e:
        logging.error(f'Failed to set up signal handler {attr_name}: {e}')
