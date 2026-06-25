/*
  ESP32 4-wheel motor straight-line test

  Upload this sketch to the ESP32. The Jetson sends serial commands over USB.

  Commands:
    PING
    STOP
    SET <fl> <fr> <bl> <br>
    RUN <base> <fl_scale> <fr_scale> <bl_scale> <br_scale> <duration_ms>

  PWM values are in the range -255..255.
  Positive/negative direction can be changed with the direction field below.
*/

#include <Arduino.h>

#if __has_include(<esp_arduino_version.h>)
#include <esp_arduino_version.h>
#endif

#ifndef ESP_ARDUINO_VERSION_MAJOR
#define ESP_ARDUINO_VERSION_MAJOR 2
#endif

struct Motor {
  const char *name;
  int pinA;
  int pinB;
  int chA;
  int chB;
  int direction;
  int currentPwm;
};

// Motor driver pins from the local pin map text file.
// FL: front-left, FR: front-right, BL: back-left, BR: back-right.
Motor motors[] = {
  {"FL", 23, 25, 0, 1, 1, 0},
  {"FR", 4, 5, 2, 3, 1, 0},
  {"BL", 2, 15, 4, 5, 1, 0},
  {"BR", 14, 13, 6, 7, 1, 0},
};

const int MOTOR_COUNT = sizeof(motors) / sizeof(motors[0]);
const int PWM_FREQ_HZ = 20000;
const int PWM_RESOLUTION_BITS = 8;
const int PWM_MAX = 255;

// If a wheel does not move at low PWM, raise this value.
// 0 means "do not force a minimum PWM".
const int MIN_MOVING_PWM = 0;

// Gentle ramping reduces sudden current spikes.
const int RAMP_STEP = 6;
const int RAMP_DELAY_MS = 6;

String inputLine;

void setupPwmPin(int pin, int channel) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttachChannel(pin, PWM_FREQ_HZ, PWM_RESOLUTION_BITS, channel);
#else
  ledcSetup(channel, PWM_FREQ_HZ, PWM_RESOLUTION_BITS);
  ledcAttachPin(pin, channel);
#endif
}

void writePwmChannel(int channel, int duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWriteChannel(channel, duty);
#else
  ledcWrite(channel, duty);
#endif
}

int clampPwm(int pwm) {
  if (pwm > PWM_MAX) return PWM_MAX;
  if (pwm < -PWM_MAX) return -PWM_MAX;
  return pwm;
}

int applyMinimumPwm(int pwm) {
  if (pwm == 0 || MIN_MOVING_PWM <= 0) return pwm;
  int sign = pwm > 0 ? 1 : -1;
  int magnitude = abs(pwm);
  if (magnitude < MIN_MOVING_PWM) magnitude = MIN_MOVING_PWM;
  return sign * magnitude;
}

void writeMotorRaw(Motor &motor, int pwm) {
  pwm = clampPwm(applyMinimumPwm(pwm)) * motor.direction;

  if (pwm > 0) {
    writePwmChannel(motor.chA, pwm);
    writePwmChannel(motor.chB, 0);
  } else if (pwm < 0) {
    writePwmChannel(motor.chA, 0);
    writePwmChannel(motor.chB, -pwm);
  } else {
    writePwmChannel(motor.chA, 0);
    writePwmChannel(motor.chB, 0);
  }
}

void setMotorPwm(Motor &motor, int targetPwm) {
  targetPwm = clampPwm(targetPwm);

  while (motor.currentPwm != targetPwm) {
    int delta = targetPwm - motor.currentPwm;
    if (abs(delta) <= RAMP_STEP) {
      motor.currentPwm = targetPwm;
    } else {
      motor.currentPwm += delta > 0 ? RAMP_STEP : -RAMP_STEP;
    }
    writeMotorRaw(motor, motor.currentPwm);
    delay(RAMP_DELAY_MS);
  }
}

void setAllMotors(int fl, int fr, int bl, int br) {
  int values[] = {fl, fr, bl, br};
  for (int i = 0; i < MOTOR_COUNT; i++) {
    setMotorPwm(motors[i], values[i]);
  }
}

void stopAllMotors() {
  setAllMotors(0, 0, 0, 0);
}

void printStatus() {
  Serial.print("PWM");
  for (int i = 0; i < MOTOR_COUNT; i++) {
    Serial.print(' ');
    Serial.print(motors[i].name);
    Serial.print('=');
    Serial.print(motors[i].currentPwm);
  }
  Serial.println();
}

int readIntToken(char *&cursor, bool &ok) {
  while (*cursor == ' ') cursor++;
  if (*cursor == '\0') {
    ok = false;
    return 0;
  }

  char *endPtr = nullptr;
  long value = strtol(cursor, &endPtr, 10);
  if (endPtr == cursor) {
    ok = false;
    return 0;
  }

  cursor = endPtr;
  return (int)value;
}

float readFloatToken(char *&cursor, bool &ok) {
  while (*cursor == ' ') cursor++;
  if (*cursor == '\0') {
    ok = false;
    return 0.0f;
  }

  char *endPtr = nullptr;
  float value = strtof(cursor, &endPtr);
  if (endPtr == cursor) {
    ok = false;
    return 0.0f;
  }

  cursor = endPtr;
  return value;
}

void handleCommand(String line) {
  line.trim();
  line.toUpperCase();
  if (line.length() == 0) return;

  char buffer[96];
  line.toCharArray(buffer, sizeof(buffer));
  char *cursor = buffer;
  char *command = strtok_r(cursor, " ", &cursor);

  if (strcmp(command, "PING") == 0) {
    Serial.println("PONG");
    return;
  }

  if (strcmp(command, "STOP") == 0) {
    stopAllMotors();
    Serial.println("OK STOP");
    return;
  }

  if (strcmp(command, "SET") == 0) {
    bool ok = true;
    int fl = readIntToken(cursor, ok);
    int fr = readIntToken(cursor, ok);
    int bl = readIntToken(cursor, ok);
    int br = readIntToken(cursor, ok);
    if (!ok) {
      Serial.println("ERR SET needs: SET <fl> <fr> <bl> <br>");
      return;
    }

    setAllMotors(fl, fr, bl, br);
    Serial.println("OK SET");
    printStatus();
    return;
  }

  if (strcmp(command, "RUN") == 0) {
    bool ok = true;
    int base = readIntToken(cursor, ok);
    float flScale = readFloatToken(cursor, ok);
    float frScale = readFloatToken(cursor, ok);
    float blScale = readFloatToken(cursor, ok);
    float brScale = readFloatToken(cursor, ok);
    int durationMs = readIntToken(cursor, ok);
    if (!ok) {
      Serial.println("ERR RUN needs: RUN <base> <fl_scale> <fr_scale> <bl_scale> <br_scale> <duration_ms>");
      return;
    }

    int fl = clampPwm((int)(base * flScale));
    int fr = clampPwm((int)(base * frScale));
    int bl = clampPwm((int)(base * blScale));
    int br = clampPwm((int)(base * brScale));

    setAllMotors(fl, fr, bl, br);
    Serial.println("OK RUN");
    printStatus();
    delay(durationMs);
    stopAllMotors();
    Serial.println("OK DONE");
    return;
  }

  if (strcmp(command, "HELP") == 0) {
    Serial.println("Commands: PING | STOP | SET <fl> <fr> <bl> <br> | RUN <base> <fl_s> <fr_s> <bl_s> <br_s> <ms>");
    return;
  }

  Serial.println("ERR unknown command. Send HELP.");
}

void setup() {
  Serial.begin(115200);
  delay(800);

  for (int i = 0; i < MOTOR_COUNT; i++) {
    setupPwmPin(motors[i].pinA, motors[i].chA);
    setupPwmPin(motors[i].pinB, motors[i].chB);
    writeMotorRaw(motors[i], 0);
  }

  Serial.println("ESP32 motor test ready. Send HELP.");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (inputLine.length() > 0) {
        handleCommand(inputLine);
        inputLine = "";
      }
    } else {
      inputLine += c;
      if (inputLine.length() > 90) {
        inputLine = "";
        Serial.println("ERR line too long");
      }
    }
  }
}
