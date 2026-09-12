#include <Arduino_RouterBridge.h>

void setup() {
  // Initialize the native bridge
  Bridge.begin();
  
  // Setup pins 2 to 5 with internal pull-down resistors!
  // This forces them to perfectly read LOW (0) until you touch them to 3.3V.
  for (int pin = 2; pin <= 5; pin++) {
    pinMode(pin, INPUT_PULLDOWN); 
  }
}

void loop() {
  String pinData = "";
  for (int pin = 2; pin <= 5; pin++) {
    pinData += String(digitalRead(pin));
    if (pin < 5) {
      pinData += ",";
    }
  }
  
  // The official command to pass data to Python is Bridge.call()
  Bridge.call("hardware_pins", pinData.c_str());
  
  delay(100);
}