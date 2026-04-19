#include <Arduino.h>
#include <ESP32Servo.h>

// Which motor to test: SWEEP_MOTOR (pin 1) or SORT_MOTOR (pin 0)
enum ServoMotorPin {
  SWEEP_MOTOR = 1,
  SORT_MOTOR = 0,
};

static constexpr int TEST_MOTOR = SORT_MOTOR;  // Change to SWEEP_MOTOR to test the other one
static constexpr int SERVO_MIN_US = 500;
static constexpr int SERVO_MAX_US = 2500;
static constexpr int SWEEP_DELAY_MS = 15;

Servo testServo;

void setup() {
  Serial.begin(115200);
  delay(500);

  testServo.setPeriodHertz(50);
  testServo.attach(TEST_MOTOR, SERVO_MIN_US, SERVO_MAX_US);
  
  Serial.println("=== SERVO CHARACTERIZATION TEST ===");
  Serial.print("Testing motor on pin: ");
  Serial.println(TEST_MOTOR);
  Serial.println("Sweeping from 500 µs to 2500 µs in 50 µs steps...");
  Serial.println("Observe servo position and note min/max extremes.");
  Serial.println("");
}

void loop() {
  // Sweep up in 50 µs increments
  for (int us = SERVO_MIN_US; us <= SERVO_MAX_US; us += 50) {
    testServo.writeMicroseconds(us);
    Serial.print("µs: ");
    Serial.print(us);
    Serial.print(" | Angle: ");
    Serial.println(testServo.read());
    delay(1500);  // 1.5s per position so you can observe
  }

  Serial.println("--- Sweep complete, reversing ---");
  delay(2000);

  // Sweep down in 50 µs increments
  for (int us = SERVO_MAX_US; us >= SERVO_MIN_US; us -= 50) {
    testServo.writeMicroseconds(us);
    Serial.print("µs: ");
    Serial.print(us);
    Serial.print(" | Angle: ");
    Serial.println(testServo.read());
    delay(1500);
  }

  Serial.println("--- Cycle complete, restarting ---");
  delay(3000);
}
