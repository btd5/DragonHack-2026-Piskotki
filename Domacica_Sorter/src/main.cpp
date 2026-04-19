#include <Arduino.h>
#include <ESP32Servo.h>

// Variable frequency (default) - LEDC preferred
ESP32PWM pwm1(true);  // or ESP32PWM pwm1(true);

// Fixed frequency - MCPWM preferred
ESP32PWM pwm2(false);  // Optimal for servos

enum ServoMotorPin {
    SWEEP_MOTOR = 1,
    SORT_MOTOR = 0,
};

static constexpr int SWEEP_SERVO_MIN_US = 600;
static constexpr int SWEEP_SERVO_MAX_US = 2400;

static constexpr int SORT_SERVO_MIN_US = 900;
static constexpr int SORT_SERVO_MAX_US = 2200;

static constexpr int SWEEP_DELAY_MS = 20;
static constexpr int MOVE_DELAY_MS = 100;

Servo Sweep_Servo;
Servo Sort_Servo;

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("Domacica Sorter Starting...");

    // Sweep servo setup
    Sweep_Servo.setPeriodHertz(50);
    Sweep_Servo.attach(SWEEP_MOTOR, SWEEP_SERVO_MIN_US, SWEEP_SERVO_MAX_US);

    Sweep_Servo.write(160);  // Start at 160 degrees

    // Sort servo setup
    Sort_Servo.setPeriodHertz(50);
    Sort_Servo.attach(SORT_MOTOR, SORT_SERVO_MIN_US, SORT_SERVO_MAX_US);

    Sort_Servo.write(90);  // Start at 90 degrees
    delay(2000);           // Wait for servos to reach position
}

void loop() {
    while (!Serial.available()) {
        delay(100);
    }
    int command = Serial.read();
    if (command >= '0' && command <= '4') {

        int sort = command - '0';  // Convert char to int (0-4)
        int sort_angle = 30 + sort * 30;  // Map 0-4 to 30, 60, 90, 120, 150 degrees
    
        Sort_Servo.write(sort_angle);

        for (int angle = 160; angle > 0; angle--) {
            Sweep_Servo.write(angle);
            delay(SWEEP_DELAY_MS);
        }

        for (int angle = 0; angle < 160; angle++) {
            Sweep_Servo.write(angle);
            delay(SWEEP_DELAY_MS);
        }
        delay(MOVE_DELAY_MS);
    
}
}