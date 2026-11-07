import 'dart:io';

/// Detects if the current iOS runtime is a Simulator or physical device.
bool get isIosSimulator {
  if (!Platform.isIOS) return false;
  return Platform.environment.containsKey('SIMULATOR_DEVICE_NAME') ||
      Platform.environment.containsKey('SIMULATOR_ROOT');
}

/// Detects if the current runtime is a physical iOS device.
bool get isIosPhysical {
  if (!Platform.isIOS) return false;
  return !isIosSimulator;
}
