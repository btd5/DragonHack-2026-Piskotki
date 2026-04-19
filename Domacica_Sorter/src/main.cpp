#include <Arduino.h>
#include <ESP32Servo.h>

// Variable frequency (default) - LEDC preferred
ESP32PWM pwm1(true);       // or ESP32PWM pwm1(true);

// Fixed frequency - MCPWM preferred
ESP32PWM pwm2(false);      // Optimal for servos

enum ServoMotorPin {
  SWEEP_MOTOR = 1,
  SORT_MOTOR = 0,
};

static constexpr int SWEEP_SERVO_MIN_US = 600;
static constexpr int SWEEP_SERVO_MAX_US = 2400;

static constexpr int SORT_SERVO_MIN_US = 900;
static constexpr int SORT_SERVO_MAX_US = 2200;


static constexpr int MOVE_DELAY_MS = 20;

Servo Sweep_Servo;
Servo Sort_Servo;

void setup() {
  Serial.begin(115200);
  delay(500);

  // Sweep servo setup
  Sweep_Servo.setPeriodHertz(50);
  Sweep_Servo.attach(SWEEP_MOTOR, SWEEP_SERVO_MIN_US, SWEEP_SERVO_MAX_US);

  Sweep_Servo.write(180); // Start at 0 degrees

  // Sort servo setup
  Sort_Servo.setPeriodHertz(50);
  Sort_Servo.attach(SORT_MOTOR, SORT_SERVO_MIN_US, SORT_SERVO_MAX_US);

  Sort_Servo.write(90); // Start at 90 degrees
  delay(2000); // Wait for servos to reach position



  // for (int angle = 180; angle >= 70; angle--) {
  //   Sweep_Servo.write(angle);
  //   delay(SWEEP_DELAY_MS);
  // }

  // Sort_Servo.write(0); // Move to 0 degrees
  // delay(2000); // Wait for servo to reach position  

  // Sort_Servo.write(90); // Move back to 90 degrees
  // delay(2000); // Wait for servo to reach position

  // Sort_Servo.write(180); // Move to 180 degrees
  // delay(2000); // Wait for servo to reach position

}

void loop() {
  // for (int angle = 0; angle <= 180; angle++) {
  //   Sweep_Servo.write(angle);
  //   delay(SWEEP_DELAY_MS);
  // }

  // for (int angle = 180; angle >= 0; angle--) {
  //   Sweep_Servo.write(angle);
  //   delay(SWEEP_DELAY_MS);
 // }
}