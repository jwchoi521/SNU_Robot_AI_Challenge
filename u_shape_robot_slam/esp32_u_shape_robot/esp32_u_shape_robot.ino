/*
  ESP32 U-shape robot controller.

  Hardware strategy:
    - No gripper.
    - The U-shape body traps objects inside the robot.
    - Two MG996R servos form the front gate.
    - One DFRobot IR break-beam sensor detects object entry.
    - Default transport batches are 3, 2, 2 objects.

  Serial commands from Jetson:
    PING
    STOP
    SET <fl> <fr> <bl> <br>
    DRIVE <base> <fl_scale> <fr_scale> <bl_scale> <br_scale>
    RUN <base> <fl_scale> <fr_scale> <bl_scale> <br_scale> <duration_ms>
    IMU ON | IMU OFF
    ZERO_YAW
    GATE OPEN | GATE CLOSE | GATE?
    CARGO? | CARGO RESET
    BATCH <0|1|2>
    CAPACITY <1..3>
    AUTO_GATE ON | AUTO_GATE OFF
    UNLOAD
    HELP
*/

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_BNO08x.h>

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
  int targetPwm;
};

// Pin map from "pin번호 연결.txt".
Motor motors[] = {
  {"FL", 23, 25, 0, 1, -1, 0, 0},
  {"FR", 4, 5, 2, 3, 1, 0, 0},
  {"BL", 2, 15, 4, 5, -1, 0, 0},
  {"BR", 14, 13, 6, 7, 1, 0, 0},
};

const int MOTOR_COUNT = sizeof(motors) / sizeof(motors[0]);
const int PWM_FREQ_HZ = 20000;
const int PWM_RESOLUTION_BITS = 8;
const int PWM_MAX = 255;
const int MIN_MOVING_PWM = 0;
const int RAMP_STEP = 6;
const int RAMP_DELAY_MS = 6;

const int I2C_SDA_PIN = 21;
const int I2C_SCL_PIN = 22;
const uint32_t IMU_REPORT_INTERVAL_US = 20000;
const uint32_t IMU_PRINT_INTERVAL_MS = 50;

const int LEFT_GATE_SERVO_PIN = 33;
const int RIGHT_GATE_SERVO_PIN = 12;
const int LEFT_GATE_SERVO_CH = 8;
const int RIGHT_GATE_SERVO_CH = 9;
const int SERVO_FREQ_HZ = 50;
const int SERVO_RESOLUTION_BITS = 16;
const int SERVO_MIN_US = 500;
const int SERVO_MAX_US = 2500;
const int SERVO_PERIOD_US = 20000;

// Tune these four angles on the real gate before driving.
const int LEFT_GATE_CLOSED_DEG = 25;
const int LEFT_GATE_OPEN_DEG = 105;
const int RIGHT_GATE_CLOSED_DEG = 155;
const int RIGHT_GATE_OPEN_DEG = 75;

const int IR_BEAM_PIN = 35;
const bool IR_ACTIVE_LOW = true;  // Most break-beam receivers output LOW when blocked.
const uint32_t IR_DEBOUNCE_MS = 45;
const uint32_t ENTRY_CLOSE_DELAY_MS = 250;
const int MAX_CARGO_CAPACITY = 3;
const int BATCH_CAPACITIES[] = {3, 2, 2};
const int BATCH_COUNT = sizeof(BATCH_CAPACITIES) / sizeof(BATCH_CAPACITIES[0]);

String inputLine;
uint32_t lastRampMs = 0;
bool timedRunActive = false;
uint32_t timedRunStopAtMs = 0;

Adafruit_BNO08x bno08x(-1);
sh2_SensorValue_t sensorValue;
bool imuReady = false;
bool imuStreaming = false;
bool haveImuSample = false;
uint32_t nextImuPrintMs = 0;
float yawZeroRad = 0.0f;
float latestYawRad = 0.0f;
float latestPitchRad = 0.0f;
float latestRollRad = 0.0f;
float latestQi = 0.0f;
float latestQj = 0.0f;
float latestQk = 0.0f;
float latestQr = 1.0f;

bool gateOpen = false;
bool autoGateEnabled = true;
int activeBatchIndex = 0;
int targetCapacity = BATCH_CAPACITIES[0];
int cargoCount = 0;
bool irRawBlocked = false;
bool irStableBlocked = false;
bool countedThisBlock = false;
uint32_t irLastRawChangeMs = 0;
uint32_t scheduledGateCloseAtMs = 0;

void setupPwmPin(int pin, int channel, int freqHz, int resolutionBits) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttachChannel(pin, freqHz, resolutionBits, channel);
#else
  ledcSetup(channel, freqHz, resolutionBits);
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

void updateMotorRamp() {
  uint32_t now = millis();
  if (now - lastRampMs < RAMP_DELAY_MS) return;
  lastRampMs = now;

  for (int i = 0; i < MOTOR_COUNT; i++) {
    Motor &motor = motors[i];
    if (motor.currentPwm == motor.targetPwm) continue;

    int delta = motor.targetPwm - motor.currentPwm;
    if (abs(delta) <= RAMP_STEP) {
      motor.currentPwm = motor.targetPwm;
    } else {
      motor.currentPwm += delta > 0 ? RAMP_STEP : -RAMP_STEP;
    }
    writeMotorRaw(motor, motor.currentPwm);
  }
}

void setAllTargets(int fl, int fr, int bl, int br) {
  int values[] = {fl, fr, bl, br};
  for (int i = 0; i < MOTOR_COUNT; i++) {
    motors[i].targetPwm = clampPwm(values[i]);
  }
}

void forceStopAllMotors() {
  timedRunActive = false;
  for (int i = 0; i < MOTOR_COUNT; i++) {
    motors[i].targetPwm = 0;
    motors[i].currentPwm = 0;
    writeMotorRaw(motors[i], 0);
  }
}

void printStatus() {
  Serial.print("PWM");
  for (int i = 0; i < MOTOR_COUNT; i++) {
    Serial.print(' ');
    Serial.print(motors[i].name);
    Serial.print('=');
    Serial.print(motors[i].currentPwm);
    Serial.print('/');
    Serial.print(motors[i].targetPwm);
  }
  Serial.println();
}

uint32_t servoDutyFromUs(int pulseUs) {
  pulseUs = constrain(pulseUs, SERVO_MIN_US, SERVO_MAX_US);
  uint32_t maxDuty = (1UL << SERVO_RESOLUTION_BITS) - 1UL;
  return (uint32_t)((uint64_t)pulseUs * maxDuty / SERVO_PERIOD_US);
}

int servoPulseFromAngle(int degrees) {
  degrees = constrain(degrees, 0, 180);
  return map(degrees, 0, 180, SERVO_MIN_US, SERVO_MAX_US);
}

void writeServoAngle(int channel, int degrees) {
  writePwmChannel(channel, servoDutyFromUs(servoPulseFromAngle(degrees)));
}

void openGate() {
  writeServoAngle(LEFT_GATE_SERVO_CH, LEFT_GATE_OPEN_DEG);
  writeServoAngle(RIGHT_GATE_SERVO_CH, RIGHT_GATE_OPEN_DEG);
  gateOpen = true;
  scheduledGateCloseAtMs = 0;
  Serial.println("OK GATE OPEN");
}

void closeGate() {
  writeServoAngle(LEFT_GATE_SERVO_CH, LEFT_GATE_CLOSED_DEG);
  writeServoAngle(RIGHT_GATE_SERVO_CH, RIGHT_GATE_CLOSED_DEG);
  gateOpen = false;
  scheduledGateCloseAtMs = 0;
  Serial.println("OK GATE CLOSE");
}

void printCargoStatus() {
  Serial.print("CARGO count=");
  Serial.print(cargoCount);
  Serial.print(" target=");
  Serial.print(targetCapacity);
  Serial.print(" batch=");
  Serial.print(activeBatchIndex);
  Serial.print(" ir_blocked=");
  Serial.print(irStableBlocked ? 1 : 0);
  Serial.print(" gate=");
  Serial.print(gateOpen ? "open" : "closed");
  Serial.print(" full=");
  Serial.println(cargoCount >= targetCapacity ? 1 : 0);
}

bool readIrBlockedRaw() {
  int value = digitalRead(IR_BEAM_PIN);
  return IR_ACTIVE_LOW ? (value == LOW) : (value == HIGH);
}

void scheduleGateClose(uint32_t delayMs) {
  if (gateOpen && autoGateEnabled) {
    scheduledGateCloseAtMs = millis() + delayMs;
  }
}

void registerCargoEntry() {
  if (countedThisBlock) return;
  countedThisBlock = true;
  if (cargoCount < MAX_CARGO_CAPACITY) {
    cargoCount++;
  }
  Serial.print("EVENT CARGO_ENTRY count=");
  Serial.print(cargoCount);
  Serial.print(" target=");
  Serial.println(targetCapacity);
  scheduleGateClose(ENTRY_CLOSE_DELAY_MS);
}

void updateIrSensor() {
  uint32_t now = millis();
  bool rawBlocked = readIrBlockedRaw();

  if (rawBlocked != irRawBlocked) {
    irRawBlocked = rawBlocked;
    irLastRawChangeMs = now;
  }

  if ((now - irLastRawChangeMs) >= IR_DEBOUNCE_MS && irStableBlocked != irRawBlocked) {
    irStableBlocked = irRawBlocked;
    if (irStableBlocked) {
      Serial.println("IR BLOCKED");
      registerCargoEntry();
    } else {
      Serial.println("IR CLEAR");
      countedThisBlock = false;
    }
  }

  if (scheduledGateCloseAtMs != 0 && (int32_t)(now - scheduledGateCloseAtMs) >= 0) {
    closeGate();
  }

  if (cargoCount >= targetCapacity && gateOpen && autoGateEnabled) {
    scheduleGateClose(0);
  }
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

void computeScaledWheelPwm(
  int base,
  float flScale,
  float frScale,
  float blScale,
  float brScale,
  int &fl,
  int &fr,
  int &bl,
  int &br
) {
  fl = clampPwm((int)(base * flScale));
  fr = clampPwm((int)(base * frScale));
  bl = clampPwm((int)(base * blScale));
  br = clampPwm((int)(base * brScale));
}

float wrapPi(float angle) {
  while (angle > PI) angle -= TWO_PI;
  while (angle < -PI) angle += TWO_PI;
  return angle;
}

void quatToEuler(float qr, float qi, float qj, float qk, float &yaw, float &pitch, float &roll) {
  float sinrCosp = 2.0f * (qr * qi + qj * qk);
  float cosrCosp = 1.0f - 2.0f * (qi * qi + qj * qj);
  roll = atan2f(sinrCosp, cosrCosp);

  float sinp = 2.0f * (qr * qj - qk * qi);
  if (sinp > 1.0f) sinp = 1.0f;
  if (sinp < -1.0f) sinp = -1.0f;
  pitch = asinf(sinp);

  float sinyCosp = 2.0f * (qr * qk + qi * qj);
  float cosyCosp = 1.0f - 2.0f * (qj * qj + qk * qk);
  yaw = atan2f(sinyCosp, cosyCosp);
}

bool enableRotationVector() {
  if (!bno08x.enableReport(SH2_ROTATION_VECTOR, IMU_REPORT_INTERVAL_US)) {
    Serial.println("WARN IMU rotation vector report failed");
    return false;
  }
  return true;
}

void setupImu() {
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);

  if (!bno08x.begin_I2C(BNO08x_I2CADDR_DEFAULT, &Wire) && !bno08x.begin_I2C(0x4B, &Wire)) {
    Serial.println("WARN IMU not found");
    imuReady = false;
    return;
  }

  imuReady = enableRotationVector();
  if (imuReady) {
    Serial.println("OK IMU READY");
  }
}

void updateImu() {
  if (!imuReady) return;

  if (bno08x.wasReset()) {
    enableRotationVector();
  }

  if (bno08x.getSensorEvent(&sensorValue) && sensorValue.sensorId == SH2_ROTATION_VECTOR) {
    latestQr = sensorValue.un.rotationVector.real;
    latestQi = sensorValue.un.rotationVector.i;
    latestQj = sensorValue.un.rotationVector.j;
    latestQk = sensorValue.un.rotationVector.k;

    float yawRaw = 0.0f;
    quatToEuler(latestQr, latestQi, latestQj, latestQk, yawRaw, latestPitchRad, latestRollRad);
    if (!haveImuSample) {
      yawZeroRad = yawRaw;
    }
    latestYawRad = wrapPi(yawRaw - yawZeroRad);
    haveImuSample = true;
  }

  uint32_t now = millis();
  if (imuStreaming && haveImuSample && now >= nextImuPrintMs) {
    nextImuPrintMs = now + IMU_PRINT_INTERVAL_MS;
    Serial.print("IMU ");
    Serial.print(now);
    Serial.print(' ');
    Serial.print(latestYawRad, 6);
    Serial.print(' ');
    Serial.print(latestPitchRad, 6);
    Serial.print(' ');
    Serial.print(latestRollRad, 6);
    Serial.print(' ');
    Serial.print(latestQi, 6);
    Serial.print(' ');
    Serial.print(latestQj, 6);
    Serial.print(' ');
    Serial.print(latestQk, 6);
    Serial.print(' ');
    Serial.println(latestQr, 6);
  }
}

void uppercaseToken(char *token) {
  for (char *p = token; *p != '\0'; p++) {
    *p = toupper(*p);
  }
}

void handleGateCommand(char *&cursor) {
  char *mode = strtok_r(cursor, " ", &cursor);
  if (mode == nullptr) {
    Serial.println("ERR GATE needs: GATE OPEN|CLOSE|?");
    return;
  }
  uppercaseToken(mode);
  if (strcmp(mode, "OPEN") == 0) {
    openGate();
    return;
  }
  if (strcmp(mode, "CLOSE") == 0) {
    closeGate();
    return;
  }
  if (strcmp(mode, "?") == 0 || strcmp(mode, "STATUS") == 0) {
    printCargoStatus();
    return;
  }
  Serial.println("ERR GATE needs: GATE OPEN|CLOSE|?");
}

void handleCargoCommand(char *&cursor) {
  char *mode = strtok_r(cursor, " ", &cursor);
  if (mode == nullptr || strcmp(mode, "?") == 0) {
    printCargoStatus();
    return;
  }
  uppercaseToken(mode);
  if (strcmp(mode, "RESET") == 0) {
    cargoCount = 0;
    countedThisBlock = false;
    Serial.println("OK CARGO RESET");
    printCargoStatus();
    return;
  }
  Serial.println("ERR CARGO needs: CARGO? | CARGO RESET");
}

void handleBatchCommand(char *&cursor) {
  bool ok = true;
  int batchIndex = readIntToken(cursor, ok);
  if (!ok || batchIndex < 0 || batchIndex >= BATCH_COUNT) {
    Serial.println("ERR BATCH needs 0, 1, or 2");
    return;
  }
  activeBatchIndex = batchIndex;
  targetCapacity = BATCH_CAPACITIES[batchIndex];
  cargoCount = 0;
  countedThisBlock = false;
  closeGate();
  Serial.println("OK BATCH");
  printCargoStatus();
}

void handleCapacityCommand(char *&cursor) {
  bool ok = true;
  int value = readIntToken(cursor, ok);
  if (!ok || value < 1 || value > MAX_CARGO_CAPACITY) {
    Serial.println("ERR CAPACITY needs 1..3");
    return;
  }
  targetCapacity = value;
  Serial.println("OK CAPACITY");
  printCargoStatus();
}

void handleAutoGateCommand(char *&cursor) {
  char *mode = strtok_r(cursor, " ", &cursor);
  if (mode == nullptr) {
    Serial.println("ERR AUTO_GATE needs ON|OFF");
    return;
  }
  uppercaseToken(mode);
  if (strcmp(mode, "ON") == 0) {
    autoGateEnabled = true;
    Serial.println("OK AUTO_GATE ON");
    return;
  }
  if (strcmp(mode, "OFF") == 0) {
    autoGateEnabled = false;
    scheduledGateCloseAtMs = 0;
    Serial.println("OK AUTO_GATE OFF");
    return;
  }
  Serial.println("ERR AUTO_GATE needs ON|OFF");
}

void handleCommand(String line) {
  line.trim();
  if (line.length() == 0) return;

  char buffer[192];
  line.toCharArray(buffer, sizeof(buffer));
  char *cursor = buffer;
  char *command = strtok_r(cursor, " ", &cursor);
  if (command == nullptr) return;
  uppercaseToken(command);

  if (strcmp(command, "PING") == 0) {
    Serial.println("PONG");
    return;
  }

  if (strcmp(command, "STOP") == 0) {
    forceStopAllMotors();
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

    timedRunActive = false;
    setAllTargets(fl, fr, bl, br);
    Serial.println("OK SET");
    printStatus();
    return;
  }

  if (strcmp(command, "DRIVE") == 0 || strcmp(command, "RUN") == 0) {
    bool ok = true;
    int base = readIntToken(cursor, ok);
    float flScale = readFloatToken(cursor, ok);
    float frScale = readFloatToken(cursor, ok);
    float blScale = readFloatToken(cursor, ok);
    float brScale = readFloatToken(cursor, ok);
    int durationMs = 0;
    if (strcmp(command, "RUN") == 0) {
      durationMs = readIntToken(cursor, ok);
    }
    if (!ok) {
      Serial.println("ERR DRIVE/RUN needs: DRIVE <base> <fl_s> <fr_s> <bl_s> <br_s>");
      return;
    }

    int fl, fr, bl, br;
    computeScaledWheelPwm(base, flScale, frScale, blScale, brScale, fl, fr, bl, br);
    setAllTargets(fl, fr, bl, br);

    timedRunActive = strcmp(command, "RUN") == 0;
    timedRunStopAtMs = millis() + (uint32_t)durationMs;
    Serial.println(timedRunActive ? "OK RUN" : "OK DRIVE");
    printStatus();
    return;
  }

  if (strcmp(command, "IMU") == 0) {
    char *mode = strtok_r(cursor, " ", &cursor);
    if (mode == nullptr) {
      Serial.println("ERR IMU needs: IMU ON|OFF");
      return;
    }
    uppercaseToken(mode);
    if (strcmp(mode, "ON") == 0) {
      imuStreaming = imuReady;
      nextImuPrintMs = millis();
      Serial.println(imuReady ? "OK IMU ON" : "ERR IMU not ready");
      return;
    }
    if (strcmp(mode, "OFF") == 0) {
      imuStreaming = false;
      Serial.println("OK IMU OFF");
      return;
    }
    Serial.println("ERR IMU needs: IMU ON|OFF");
    return;
  }

  if (strcmp(command, "ZERO_YAW") == 0) {
    if (haveImuSample) {
      yawZeroRad += latestYawRad;
      latestYawRad = 0.0f;
    }
    Serial.println("OK ZERO_YAW");
    return;
  }

  if (strcmp(command, "GATE") == 0) {
    handleGateCommand(cursor);
    return;
  }

  if (strcmp(command, "CARGO?") == 0) {
    printCargoStatus();
    return;
  }

  if (strcmp(command, "CARGO") == 0) {
    handleCargoCommand(cursor);
    return;
  }

  if (strcmp(command, "BATCH") == 0) {
    handleBatchCommand(cursor);
    return;
  }

  if (strcmp(command, "CAPACITY") == 0) {
    handleCapacityCommand(cursor);
    return;
  }

  if (strcmp(command, "AUTO_GATE") == 0) {
    handleAutoGateCommand(cursor);
    return;
  }

  if (strcmp(command, "UNLOAD") == 0) {
    openGate();
    cargoCount = 0;
    countedThisBlock = false;
    Serial.println("OK UNLOAD");
    printCargoStatus();
    return;
  }

  if (strcmp(command, "HELP") == 0) {
    Serial.println("Commands: PING | STOP | SET <fl> <fr> <bl> <br> | DRIVE <base> <fl_s> <fr_s> <bl_s> <br_s> | RUN <base> <fl_s> <fr_s> <bl_s> <br_s> <ms> | IMU ON|OFF | ZERO_YAW | GATE OPEN|CLOSE|? | CARGO? | CARGO RESET | BATCH <0|1|2> | CAPACITY <1..3> | AUTO_GATE ON|OFF | UNLOAD");
    return;
  }

  Serial.println("ERR unknown command. Send HELP.");
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (inputLine.length() > 0) {
        handleCommand(inputLine);
        inputLine = "";
      }
    } else {
      inputLine += c;
      if (inputLine.length() > 180) {
        inputLine = "";
        Serial.println("ERR line too long");
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(800);

  for (int i = 0; i < MOTOR_COUNT; i++) {
    setupPwmPin(motors[i].pinA, motors[i].chA, PWM_FREQ_HZ, PWM_RESOLUTION_BITS);
    setupPwmPin(motors[i].pinB, motors[i].chB, PWM_FREQ_HZ, PWM_RESOLUTION_BITS);
    writeMotorRaw(motors[i], 0);
  }

  setupPwmPin(LEFT_GATE_SERVO_PIN, LEFT_GATE_SERVO_CH, SERVO_FREQ_HZ, SERVO_RESOLUTION_BITS);
  setupPwmPin(RIGHT_GATE_SERVO_PIN, RIGHT_GATE_SERVO_CH, SERVO_FREQ_HZ, SERVO_RESOLUTION_BITS);
  closeGate();

  pinMode(IR_BEAM_PIN, INPUT);
  irRawBlocked = readIrBlockedRaw();
  irStableBlocked = irRawBlocked;
  irLastRawChangeMs = millis();

  setupImu();
  Serial.println("ESP32 U-shape robot ready. Send HELP.");
  printCargoStatus();
}

void loop() {
  readSerialCommands();
  updateMotorRamp();
  updateImu();
  updateIrSensor();

  if (timedRunActive && (int32_t)(millis() - timedRunStopAtMs) >= 0) {
    forceStopAllMotors();
    Serial.println("OK DONE");
  }
}
