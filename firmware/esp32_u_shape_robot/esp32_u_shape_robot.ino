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
    STRAIGHT <base> <duration_ms>
    ENC? | ENC RESET | ENC ON | ENC OFF | ENC TEST <base> <duration_ms>
    IMU ON | IMU OFF
    ZERO_YAW
    GATE OPEN | GATE CLOSE | GATE?
    SERVO LEFT <deg> | SERVO RIGHT <deg> | SERVO BOTH <left_deg> <right_deg> | SERVO TEST
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
  {"FL", 4, 5, 2, 3, -1, 0, 0},
  {"FR", 23, 25, 0, 1, 1, 0, 0},
  {"BL", 14, 13, 6, 7, -1, 0, 0},
  {"BR", 2, 15, 4, 5, 1, 0, 0},
};

const int MOTOR_COUNT = sizeof(motors) / sizeof(motors[0]);
const int PWM_FREQ_HZ = 20000;
const int PWM_RESOLUTION_BITS = 8;
const int PWM_MAX = 255;
const int MIN_MOVING_PWM = 0;
const int RAMP_STEP = 6;
const int RAMP_DELAY_MS = 6;

const int ENCODER_A_PINS[] = {18, 16, 32, 26};  // FL, FR, BL, BR
const int ENCODER_B_PINS[] = {19, 17, 34, 27};  // GPIO34 is input-only and has no internal pull-up.
const int ENCODER_DIRECTIONS[] = {1, 1, 1, -1};
volatile int32_t encoderTicks[MOTOR_COUNT] = {0, 0, 0, 0};
const uint32_t ENCODER_PRINT_INTERVAL_MS = 200;

const float FIXED_WHEEL_SCALE_FL = 1.17f;
const float FIXED_WHEEL_SCALE_FR = 0.89f;
const float FIXED_WHEEL_SCALE_BL = 1.11f;
const float FIXED_WHEEL_SCALE_BR = 0.89f;

const uint32_t STRAIGHT_CONTROL_INTERVAL_MS = 25;
const float STRAIGHT_WHEEL_KP = 3.5f;
const int STRAIGHT_CORRECTION_DIRECTION = 1;
const bool STRAIGHT_ENABLE_ENCODER_CORRECTION = true;
const int STRAIGHT_MAX_CORRECTION = 35;
const uint32_t STRAIGHT_DEBUG_INTERVAL_MS = 250;

const uint32_t SET_CONTROL_INTERVAL_MS = 25;
const float SET_WHEEL_KP = 3.5f;
const float SET_WHEEL_KI = 0.08f;
const int SET_MAX_CORRECTION = 35;
const float SET_INTEGRAL_LIMIT = 250.0f;
const uint32_t SET_DEBUG_INTERVAL_MS = 250;

const uint32_t SET1_CONTROL_INTERVAL_MS = 25;
const int SET1_STATIC_FRICTION_PWM = 50;
const float SET1_FEED_FORWARD_PWM_PER_CPS = 0.042f;
const float SET1_WHEEL_KP = 0.045f;
const float SET1_WHEEL_KI = 0.35f;
const int SET1_MAX_CORRECTION = 90;
const float SET1_INTEGRAL_LIMIT = 250.0f;
const float SET1_MAX_TARGET_CPS = 2834.0f;  // 20 rad/s * 141.7 counts/rad.
const uint32_t SET1_DEBUG_INTERVAL_MS = 250;
const bool SET1_IMU_YAW_FEEDBACK_ENABLED = true;
const float SET1_WHEEL_RADIUS_M = 0.033f;
const float SET1_TRACK_WIDTH_M = 0.30f;
const float SET1_ENCODER_COUNTS_PER_REV = 890.3f;
const float SET1_IMU_YAW_RATE_SIGN = 1.0f;
const uint32_t SET1_IMU_YAW_RATE_TIMEOUT_MS = 250;
const float SET1_YAW_FEEDBACK_KP = 0.6f;
const float SET1_YAW_FEEDBACK_KI = 0.0f;
const float SET1_YAW_FEEDBACK_INTEGRAL_LIMIT = 0.5f;
const float SET1_YAW_FEEDBACK_MAX_CORRECTION_RAD_S = 0.35f;
const float SET1_YAW_RATE_ERROR_DEADBAND_RAD_S = 0.02f;

const int I2C_SDA_PIN = 21;
const int I2C_SCL_PIN = 22;
const uint32_t IMU_REPORT_INTERVAL_US = 20000;
const uint32_t IMU_PRINT_INTERVAL_MS = 50;

const int LEFT_GATE_SERVO_PIN = 33;
const int RIGHT_GATE_SERVO_PIN = 12;
const int SERVO_MIN_US = 500;
const int SERVO_MAX_US = 2500;
const int SERVO_PERIOD_US = 20000;
const uint32_t SERVO_HOLD_AFTER_MOVE_MS = 900;

// Tune these four angles on the real gate before driving.
const int LEFT_GATE_CLOSED_DEG = 110;
const int LEFT_GATE_OPEN_DEG = 20;
const int RIGHT_GATE_CLOSED_DEG = 20;
const int RIGHT_GATE_OPEN_DEG = 110;

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
bool setPwmControlActive = false;
uint32_t nextSetControlMs = 0;
uint32_t nextSetDebugMs = 0;
int setBaseTargets[MOTOR_COUNT] = {0, 0, 0, 0};
int32_t setLastTicks[MOTOR_COUNT] = {0, 0, 0, 0};
float setIntegral[MOTOR_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
bool set1VelocityControlActive = false;
uint32_t lastSet1ControlMs = 0;
uint32_t nextSet1ControlMs = 0;
uint32_t nextSet1DebugMs = 0;
float set1TargetCps[MOTOR_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
float set1Integral[MOTOR_COUNT] = {0.0f, 0.0f, 0.0f, 0.0f};
int32_t set1LastTicks[MOTOR_COUNT] = {0, 0, 0, 0};
float set1YawFeedbackIntegral = 0.0f;
bool straightRunActive = false;
uint32_t straightRunStopAtMs = 0;
uint32_t nextStraightControlMs = 0;
uint32_t nextStraightDebugMs = 0;
int straightBasePwm = 0;
int straightBaseTargets[MOTOR_COUNT] = {0, 0, 0, 0};
int32_t straightLastTicks[MOTOR_COUNT] = {0, 0, 0, 0};
bool encoderStreaming = false;
uint32_t nextEncoderPrintMs = 0;

Adafruit_BNO08x bno08x(-1);
sh2_SensorValue_t sensorValue;
bool imuReady = false;
bool imuStreaming = false;
bool imuRequested = false;
bool haveImuSample = false;
bool haveImuYawRateReference = false;
bool haveImuYawRateSample = false;
uint32_t nextImuPrintMs = 0;
uint32_t latestImuSampleMs = 0;
uint32_t lastYawRateUs = 0;
float yawZeroRad = 0.0f;
float latestYawRad = 0.0f;
float latestImuWzRadS = 0.0f;
float lastYawRateYawRad = 0.0f;
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

struct SoftwareServo {
  int pin;
  int pulseUs;
  bool pulseHigh;
  uint32_t cycleStartUs;
  uint32_t pulseEndUs;
};

SoftwareServo leftGateServo = {LEFT_GATE_SERVO_PIN, 1500, false, 0, 0};
SoftwareServo rightGateServo = {RIGHT_GATE_SERVO_PIN, 1500, false, 0, 0};
bool servosEnabled = false;
uint32_t servosActiveUntilMs = 0;

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

bool isInputOnlyNoPullupPin(int pin) {
  return pin >= 34 && pin <= 39;
}

void IRAM_ATTR updateEncoderFromA(int index) {
  int a = digitalRead(ENCODER_A_PINS[index]);
  int b = digitalRead(ENCODER_B_PINS[index]);
  int delta = (a == b) ? 1 : -1;
  encoderTicks[index] += delta * ENCODER_DIRECTIONS[index];
}

void IRAM_ATTR handleFlEncoderA() {
  updateEncoderFromA(0);
}

void IRAM_ATTR handleFrEncoderA() {
  updateEncoderFromA(1);
}

void IRAM_ATTR handleBlEncoderA() {
  updateEncoderFromA(2);
}

void IRAM_ATTR handleBrEncoderA() {
  updateEncoderFromA(3);
}

void readEncoderTicks(int32_t *outTicks) {
  noInterrupts();
  for (int i = 0; i < MOTOR_COUNT; i++) {
    // Multiply by 1.3 to compensate for the robot physically moving 1.3x faster
    // than the target speed (likely due to a wheel size or gear ratio mismatch).
    // This scales up the perceived encoder counts, so the PID loop outputs a slower PWM,
    // and ROS2 receives the exact requested counts, keeping odometry perfectly accurate.
    outTicks[i] = (int32_t)(encoderTicks[i] * 1.3f);
  }
  interrupts();
}

void resetEncoderTicks() {
  noInterrupts();
  for (int i = 0; i < MOTOR_COUNT; i++) {
    encoderTicks[i] = 0;
  }
  interrupts();
}

void printEncoderStatus() {
  int32_t ticks[MOTOR_COUNT];
  readEncoderTicks(ticks);

  Serial.print("ENC");
  for (int i = 0; i < MOTOR_COUNT; i++) {
    Serial.print(' ');
    Serial.print(motors[i].name);
    Serial.print('=');
    Serial.print(ticks[i]);
  }
  Serial.println();
}

void updateEncoderStreaming() {
  if (!encoderStreaming) return;
  uint32_t now = millis();
  if ((int32_t)(now - nextEncoderPrintMs) < 0) return;
  nextEncoderPrintMs = now + ENCODER_PRINT_INTERVAL_MS;
  printEncoderStatus();
}

void setupEncoders() {
  for (int i = 0; i < MOTOR_COUNT; i++) {
    pinMode(ENCODER_A_PINS[i], isInputOnlyNoPullupPin(ENCODER_A_PINS[i]) ? INPUT : INPUT_PULLUP);
    pinMode(ENCODER_B_PINS[i], isInputOnlyNoPullupPin(ENCODER_B_PINS[i]) ? INPUT : INPUT_PULLUP);
  }

  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PINS[0]), handleFlEncoderA, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PINS[1]), handleFrEncoderA, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PINS[2]), handleBlEncoderA, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_A_PINS[3]), handleBrEncoderA, CHANGE);
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

float clampFloat(float value, float low, float high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

int roundFloatToInt(float value) {
  return value >= 0.0f ? (int)(value + 0.5f) : (int)(value - 0.5f);
}

float fixedWheelScaleForIndex(int index) {
  if (index == 0) return FIXED_WHEEL_SCALE_FL;
  if (index == 1) return FIXED_WHEEL_SCALE_FR;
  if (index == 2) return FIXED_WHEEL_SCALE_BL;
  return FIXED_WHEEL_SCALE_BR;
}

void resetSetPwmControlState() {
  setPwmControlActive = false;
  nextSetControlMs = 0;
  nextSetDebugMs = 0;
  for (int i = 0; i < MOTOR_COUNT; i++) {
    setBaseTargets[i] = 0;
    setLastTicks[i] = 0;
    setIntegral[i] = 0.0f;
  }
}

void resetSet1VelocityControlState() {
  set1VelocityControlActive = false;
  lastSet1ControlMs = 0;
  nextSet1ControlMs = 0;
  nextSet1DebugMs = 0;
  set1YawFeedbackIntegral = 0.0f;
  for (int i = 0; i < MOTOR_COUNT; i++) {
    set1TargetCps[i] = 0.0f;
    set1Integral[i] = 0.0f;
    set1LastTicks[i] = 0;
  }
}

void forceStopAllMotors() {
  timedRunActive = false;
  resetSetPwmControlState();
  resetSet1VelocityControlState();
  straightRunActive = false;
  for (int i = 0; i < MOTOR_COUNT; i++) {
    motors[i].targetPwm = 0;
    motors[i].currentPwm = 0;
    writeMotorRaw(motors[i], 0);
  }
}

int32_t absoluteDelta(int32_t current, int32_t previous) {
  int32_t delta = current - previous;
  return delta < 0 ? -delta : delta;
}

void startStraightRun(int basePwm, int durationMs) {
  basePwm = clampPwm(basePwm);
  if (basePwm == 0 || durationMs <= 0) {
    Serial.println("ERR STRAIGHT needs nonzero base and positive duration_ms");
    return;
  }

  timedRunActive = false;
  straightRunActive = true;
  straightBasePwm = basePwm;
  straightRunStopAtMs = millis() + (uint32_t)durationMs;
  nextStraightControlMs = millis() + STRAIGHT_CONTROL_INTERVAL_MS;
  nextStraightDebugMs = millis() + STRAIGHT_DEBUG_INTERVAL_MS;
  readEncoderTicks(straightLastTicks);
  computeScaledWheelPwm(
    basePwm,
    FIXED_WHEEL_SCALE_FL,
    FIXED_WHEEL_SCALE_FR,
    FIXED_WHEEL_SCALE_BL,
    FIXED_WHEEL_SCALE_BR,
    straightBaseTargets[0],
    straightBaseTargets[1],
    straightBaseTargets[2],
    straightBaseTargets[3]
  );
  setAllTargets(
    straightBaseTargets[0],
    straightBaseTargets[1],
    straightBaseTargets[2],
    straightBaseTargets[3]
  );
  Serial.println("OK STRAIGHT");
  printStatus();
}

void applyFixedWheelCompensation(
  int fl,
  int fr,
  int bl,
  int br,
  int &outFl,
  int &outFr,
  int &outBl,
  int &outBr
) {
  outFl = clampPwm((int)(fl * FIXED_WHEEL_SCALE_FL));
  outFr = clampPwm((int)(fr * FIXED_WHEEL_SCALE_FR));
  outBl = clampPwm((int)(bl * FIXED_WHEEL_SCALE_BL));
  outBr = clampPwm((int)(br * FIXED_WHEEL_SCALE_BR));
}

void startSetClosedLoop(int fl, int fr, int bl, int br) {
  timedRunActive = false;
  straightRunActive = false;
  resetSet1VelocityControlState();
  setPwmControlActive = true;
  nextSetControlMs = millis() + SET_CONTROL_INTERVAL_MS;
  nextSetDebugMs = millis() + SET_DEBUG_INTERVAL_MS;

  applyFixedWheelCompensation(
    fl,
    fr,
    bl,
    br,
    setBaseTargets[0],
    setBaseTargets[1],
    setBaseTargets[2],
    setBaseTargets[3]
  );

  readEncoderTicks(setLastTicks);
  for (int i = 0; i < MOTOR_COUNT; i++) {
    setIntegral[i] = 0.0f;
  }

  setAllTargets(
    setBaseTargets[0],
    setBaseTargets[1],
    setBaseTargets[2],
    setBaseTargets[3]
  );
  Serial.println("OK SET");
  printStatus();
}

void updateSetClosedLoop() {
  if (!setPwmControlActive) return;

  uint32_t now = millis();
  if ((int32_t)(now - nextSetControlMs) < 0) return;
  nextSetControlMs = now + SET_CONTROL_INTERVAL_MS;

  int32_t ticks[MOTOR_COUNT];
  int32_t wheelDelta[MOTOR_COUNT];
  readEncoderTicks(ticks);
  for (int i = 0; i < MOTOR_COUNT; i++) {
    wheelDelta[i] = absoluteDelta(ticks[i], setLastTicks[i]);
    setLastTicks[i] = ticks[i];
  }

  int32_t averageTicks = 0;
  for (int i = 0; i < MOTOR_COUNT; i++) {
    averageTicks += wheelDelta[i];
  }
  averageTicks /= MOTOR_COUNT;

  int wheelPwm[MOTOR_COUNT];
  int wheelCorrection[MOTOR_COUNT];
  for (int i = 0; i < MOTOR_COUNT; i++) {
    int baseSign = setBaseTargets[i] >= 0 ? 1 : -1;
    if (setBaseTargets[i] == 0) {
      baseSign = 0;
    }

    wheelCorrection[i] = 0;
    if (baseSign != 0) {
      int32_t error = averageTicks - wheelDelta[i];
      setIntegral[i] = constrain(
        setIntegral[i] + (float)error,
        -SET_INTEGRAL_LIMIT,
        SET_INTEGRAL_LIMIT
      );
      float correction = error * SET_WHEEL_KP + setIntegral[i] * SET_WHEEL_KI;
      wheelCorrection[i] = constrain(
        (int)correction,
        -SET_MAX_CORRECTION,
        SET_MAX_CORRECTION
      );
    } else {
      setIntegral[i] = 0.0f;
    }

    wheelPwm[i] = clampPwm(setBaseTargets[i] + baseSign * wheelCorrection[i]);
  }

  setAllTargets(wheelPwm[0], wheelPwm[1], wheelPwm[2], wheelPwm[3]);

  if ((int32_t)(now - nextSetDebugMs) >= 0) {
    nextSetDebugMs = now + SET_DEBUG_INTERVAL_MS;
    Serial.print("SET_DBG avg=");
    Serial.print(averageTicks);
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" d");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(wheelDelta[i]);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" base");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(setBaseTargets[i]);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" corr");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(wheelCorrection[i]);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" pwm");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(wheelPwm[i]);
    }
    Serial.println();
  }
}

int set1FeedForwardPwm(int index, float targetCps) {
  if (fabsf(targetCps) < 1.0f) {
    return 0;
  }
  float direction = targetCps > 0.0f ? 1.0f : -1.0f;
  float staticPwm = direction * SET1_STATIC_FRICTION_PWM;
  float velocityPwm = targetCps * SET1_FEED_FORWARD_PWM_PER_CPS;
  float pwm = (staticPwm + velocityPwm) * fixedWheelScaleForIndex(index);
  return clampPwm(roundFloatToInt(pwm));
}

void startSet1VelocityClosedLoop(float flCps, float frCps, float blCps, float brCps) {
  timedRunActive = false;
  straightRunActive = false;
  resetSetPwmControlState();
  set1VelocityControlActive = true;

  float values[] = {flCps, frCps, blCps, brCps};
  for (int i = 0; i < MOTOR_COUNT; i++) {
    set1TargetCps[i] = clampFloat(values[i], -SET1_MAX_TARGET_CPS, SET1_MAX_TARGET_CPS);
    set1Integral[i] = 0.0f;
  }

  uint32_t now = millis();
  lastSet1ControlMs = now;
  nextSet1ControlMs = now + SET1_CONTROL_INTERVAL_MS;
  nextSet1DebugMs = now + SET1_DEBUG_INTERVAL_MS;
  readEncoderTicks(set1LastTicks);

  int initialPwm[MOTOR_COUNT];
  for (int i = 0; i < MOTOR_COUNT; i++) {
    initialPwm[i] = set1FeedForwardPwm(i, set1TargetCps[i]);
  }
  setAllTargets(initialPwm[0], initialPwm[1], initialPwm[2], initialPwm[3]);
  Serial.println("OK SET1");
  printStatus();
}

void updateSet1VelocityClosedLoop() {
  if (!set1VelocityControlActive) return;

  uint32_t now = millis();
  if ((int32_t)(now - nextSet1ControlMs) < 0) return;

  float dtSec = (now - lastSet1ControlMs) * 0.001f;
  if (dtSec <= 0.0f) {
    dtSec = SET1_CONTROL_INTERVAL_MS * 0.001f;
  }
  lastSet1ControlMs = now;
  nextSet1ControlMs = now + SET1_CONTROL_INTERVAL_MS;

  int32_t ticks[MOTOR_COUNT];
  int32_t wheelDelta[MOTOR_COUNT];
  float measuredCps[MOTOR_COUNT];
  readEncoderTicks(ticks);
  for (int i = 0; i < MOTOR_COUNT; i++) {
    wheelDelta[i] = ticks[i] - set1LastTicks[i];
    set1LastTicks[i] = ticks[i];
    measuredCps[i] = (float)wheelDelta[i] / dtSec;
  }

  float adjustedTargetCps[MOTOR_COUNT];
  bool hasWheelTarget = false;
  for (int i = 0; i < MOTOR_COUNT; i++) {
    adjustedTargetCps[i] = set1TargetCps[i];
    if (fabsf(set1TargetCps[i]) >= 1.0f) {
      hasWheelTarget = true;
    }
  }

  float targetWzRadS = yawRateFromWheelCps(set1TargetCps);
  float imuWzRadS = 0.0f;
  float yawErrorRadS = 0.0f;
  float yawCorrectionRadS = 0.0f;
  float yawCorrectionCps = 0.0f;
  bool yawFeedbackActive = false;

  if (SET1_IMU_YAW_FEEDBACK_ENABLED && hasWheelTarget && haveImuYawRateSample) {
    uint32_t imuAgeMs = now - latestImuSampleMs;
    if (imuAgeMs <= SET1_IMU_YAW_RATE_TIMEOUT_MS) {
      imuWzRadS = SET1_IMU_YAW_RATE_SIGN * latestImuWzRadS;
      yawErrorRadS = targetWzRadS - imuWzRadS;
      if (fabsf(yawErrorRadS) < SET1_YAW_RATE_ERROR_DEADBAND_RAD_S) {
        yawErrorRadS = 0.0f;
      }

      set1YawFeedbackIntegral = clampFloat(
        set1YawFeedbackIntegral + yawErrorRadS * dtSec,
        -SET1_YAW_FEEDBACK_INTEGRAL_LIMIT,
        SET1_YAW_FEEDBACK_INTEGRAL_LIMIT
      );
      yawCorrectionRadS = yawErrorRadS * SET1_YAW_FEEDBACK_KP
          + set1YawFeedbackIntegral * SET1_YAW_FEEDBACK_KI;
      yawCorrectionRadS = clampFloat(
        yawCorrectionRadS,
        -SET1_YAW_FEEDBACK_MAX_CORRECTION_RAD_S,
        SET1_YAW_FEEDBACK_MAX_CORRECTION_RAD_S
      );
      yawCorrectionCps = yawRateCorrectionToSideCps(yawCorrectionRadS);

      adjustedTargetCps[0] = clampFloat(set1TargetCps[0] - yawCorrectionCps, -SET1_MAX_TARGET_CPS, SET1_MAX_TARGET_CPS);
      adjustedTargetCps[1] = clampFloat(set1TargetCps[1] + yawCorrectionCps, -SET1_MAX_TARGET_CPS, SET1_MAX_TARGET_CPS);
      adjustedTargetCps[2] = clampFloat(set1TargetCps[2] - yawCorrectionCps, -SET1_MAX_TARGET_CPS, SET1_MAX_TARGET_CPS);
      adjustedTargetCps[3] = clampFloat(set1TargetCps[3] + yawCorrectionCps, -SET1_MAX_TARGET_CPS, SET1_MAX_TARGET_CPS);
      yawFeedbackActive = true;
    } else {
      set1YawFeedbackIntegral = 0.0f;
    }
  } else {
    set1YawFeedbackIntegral = 0.0f;
  }

  int wheelPwm[MOTOR_COUNT];
  int wheelCorrection[MOTOR_COUNT];
  for (int i = 0; i < MOTOR_COUNT; i++) {
    wheelCorrection[i] = 0;
    if (fabsf(adjustedTargetCps[i]) < 1.0f) {
      set1Integral[i] = 0.0f;
      wheelPwm[i] = 0;
      continue;
    }

    float error = adjustedTargetCps[i] - measuredCps[i];
    set1Integral[i] = clampFloat(
      set1Integral[i] + error * dtSec,
      -SET1_INTEGRAL_LIMIT,
      SET1_INTEGRAL_LIMIT
    );
    float correction = error * SET1_WHEEL_KP + set1Integral[i] * SET1_WHEEL_KI;
    wheelCorrection[i] = constrain(
      roundFloatToInt(correction),
      -SET1_MAX_CORRECTION,
      SET1_MAX_CORRECTION
    );

    int feedForward = set1FeedForwardPwm(i, adjustedTargetCps[i]);
    wheelPwm[i] = clampPwm(feedForward + wheelCorrection[i]);
  }

  setAllTargets(wheelPwm[0], wheelPwm[1], wheelPwm[2], wheelPwm[3]);

  if ((int32_t)(now - nextSet1DebugMs) >= 0) {
    nextSet1DebugMs = now + SET1_DEBUG_INTERVAL_MS;
    Serial.print("SET1_DBG dt=");
    Serial.print(dtSec, 3);
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" target");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(set1TargetCps[i], 1);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" adj");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(adjustedTargetCps[i], 1);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" measured");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(measuredCps[i], 1);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" d");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(wheelDelta[i]);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" corr");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(wheelCorrection[i]);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" pwm");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(wheelPwm[i]);
    }
    Serial.print(" target_wz=");
    Serial.print(targetWzRadS, 3);
    Serial.print(" imu_wz=");
    Serial.print(imuWzRadS, 3);
    Serial.print(" yaw_err=");
    Serial.print(yawErrorRadS, 3);
    Serial.print(" yaw_corr=");
    Serial.print(yawCorrectionRadS, 3);
    Serial.print(" yaw_corr_cps=");
    Serial.print(yawCorrectionCps, 1);
    Serial.print(" yaw_fb=");
    Serial.print(yawFeedbackActive ? 1 : 0);
    Serial.println();
  }
}

void updateStraightRun() {
  if (!straightRunActive) return;

  uint32_t now = millis();
  if ((int32_t)(now - straightRunStopAtMs) >= 0) {
    forceStopAllMotors();
    Serial.println("OK DONE");
    return;
  }

  if ((int32_t)(now - nextStraightControlMs) < 0) return;
  nextStraightControlMs = now + STRAIGHT_CONTROL_INTERVAL_MS;

  int32_t ticks[MOTOR_COUNT];
  int32_t wheelDelta[MOTOR_COUNT];
  readEncoderTicks(ticks);
  for (int i = 0; i < MOTOR_COUNT; i++) {
    wheelDelta[i] = absoluteDelta(ticks[i], straightLastTicks[i]);
    straightLastTicks[i] = ticks[i];
  }

  int32_t averageTicks = 0;
  for (int i = 0; i < MOTOR_COUNT; i++) {
    averageTicks += wheelDelta[i];
  }
  averageTicks /= MOTOR_COUNT;

  int driveSign = straightBasePwm >= 0 ? 1 : -1;
  int wheelPwm[MOTOR_COUNT];
  int wheelCorrection[MOTOR_COUNT];
  for (int i = 0; i < MOTOR_COUNT; i++) {
    wheelCorrection[i] = 0;
    if (STRAIGHT_ENABLE_ENCODER_CORRECTION) {
      int32_t error = averageTicks - wheelDelta[i];
      wheelCorrection[i] = constrain((int)(error * STRAIGHT_WHEEL_KP * STRAIGHT_CORRECTION_DIRECTION), -STRAIGHT_MAX_CORRECTION, STRAIGHT_MAX_CORRECTION);
    }
    wheelPwm[i] = clampPwm(straightBaseTargets[i] + driveSign * wheelCorrection[i]);
  }

  setAllTargets(wheelPwm[0], wheelPwm[1], wheelPwm[2], wheelPwm[3]);

  if ((int32_t)(now - nextStraightDebugMs) >= 0) {
    nextStraightDebugMs = now + STRAIGHT_DEBUG_INTERVAL_MS;
    Serial.print("STRAIGHT_DBG avg=");
    Serial.print(averageTicks);
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" d");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(wheelDelta[i]);
    }
    for (int i = 0; i < MOTOR_COUNT; i++) {
      Serial.print(" pwm");
      Serial.print(motors[i].name);
      Serial.print('=');
      Serial.print(wheelPwm[i]);
    }
    Serial.println();
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

int servoPulseFromAngle(int degrees) {
  degrees = constrain(degrees, 0, 180);
  return map(degrees, 0, 180, SERVO_MIN_US, SERVO_MAX_US);
}

void updateSoftwareServo(SoftwareServo &servo, uint32_t nowUs) {
  if (servo.cycleStartUs == 0 || (int32_t)(nowUs - servo.cycleStartUs) >= SERVO_PERIOD_US) {
    servo.cycleStartUs = nowUs;
    servo.pulseEndUs = nowUs + (uint32_t)servo.pulseUs;
    servo.pulseHigh = true;
    digitalWrite(servo.pin, HIGH);
    return;
  }

  if (servo.pulseHigh && (int32_t)(nowUs - servo.pulseEndUs) >= 0) {
    servo.pulseHigh = false;
    digitalWrite(servo.pin, LOW);
  }
}

void disableServos() {
  servosEnabled = false;
  leftGateServo.pulseHigh = false;
  rightGateServo.pulseHigh = false;
  leftGateServo.cycleStartUs = 0;
  rightGateServo.cycleStartUs = 0;
  digitalWrite(leftGateServo.pin, LOW);
  digitalWrite(rightGateServo.pin, LOW);
}

void armServos(uint32_t holdMs) {
  servosEnabled = true;
  servosActiveUntilMs = millis() + holdMs;
  leftGateServo.cycleStartUs = 0;
  rightGateServo.cycleStartUs = 0;
}

void updateServos() {
  if (!servosEnabled) return;
  if ((int32_t)(millis() - servosActiveUntilMs) >= 0) {
    disableServos();
    return;
  }

  uint32_t nowUs = micros();
  updateSoftwareServo(leftGateServo, nowUs);
  updateSoftwareServo(rightGateServo, nowUs);
}

void holdServos(uint32_t durationMs) {
  armServos(durationMs + 50);
  uint32_t startMs = millis();
  while ((uint32_t)(millis() - startMs) < durationMs) {
    updateServos();
    delay(1);
  }
}

void writeServoAngle(SoftwareServo &servo, int degrees) {
  servo.pulseUs = servoPulseFromAngle(degrees);
  armServos(SERVO_HOLD_AFTER_MOVE_MS);
}

void openGate() {
  writeServoAngle(leftGateServo, LEFT_GATE_OPEN_DEG);
  writeServoAngle(rightGateServo, RIGHT_GATE_OPEN_DEG);
  gateOpen = true;
  scheduledGateCloseAtMs = 0;
  Serial.println("OK GATE OPEN");
}

void closeGate() {
  writeServoAngle(leftGateServo, LEFT_GATE_CLOSED_DEG);
  writeServoAngle(rightGateServo, RIGHT_GATE_CLOSED_DEG);
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
  (void)flScale;
  (void)frScale;
  (void)blScale;
  (void)brScale;
  fl = clampPwm((int)(base * FIXED_WHEEL_SCALE_FL));
  fr = clampPwm((int)(base * FIXED_WHEEL_SCALE_FR));
  bl = clampPwm((int)(base * FIXED_WHEEL_SCALE_BL));
  br = clampPwm((int)(base * FIXED_WHEEL_SCALE_BR));
}

float wrapPi(float angle) {
  while (angle > PI) angle -= TWO_PI;
  while (angle < -PI) angle += TWO_PI;
  return angle;
}

float cpsToRadPerSec(float countsPerSec) {
  return countsPerSec * TWO_PI / SET1_ENCODER_COUNTS_PER_REV;
}

float radPerSecToCps(float radPerSec) {
  return radPerSec * SET1_ENCODER_COUNTS_PER_REV / TWO_PI;
}

float yawRateFromWheelCps(const float *wheelCps) {
  float leftRadS = 0.5f * (cpsToRadPerSec(wheelCps[0]) + cpsToRadPerSec(wheelCps[2]));
  float rightRadS = 0.5f * (cpsToRadPerSec(wheelCps[1]) + cpsToRadPerSec(wheelCps[3]));
  return (rightRadS - leftRadS) * SET1_WHEEL_RADIUS_M / SET1_TRACK_WIDTH_M;
}

float yawRateCorrectionToSideCps(float yawRateCorrectionRadS) {
  float sideRadS = yawRateCorrectionRadS * SET1_TRACK_WIDTH_M / (2.0f * SET1_WHEEL_RADIUS_M);
  return radPerSecToCps(sideRadS);
}

void resetImuYawRateEstimator() {
  haveImuYawRateReference = false;
  haveImuYawRateSample = false;
  latestImuWzRadS = 0.0f;
  lastYawRateUs = micros();
  lastYawRateYawRad = latestYawRad;
}

void updateImuYawRate(float yawRad) {
  uint32_t nowUs = micros();

  if (!haveImuYawRateReference) {
    lastYawRateYawRad = yawRad;
    lastYawRateUs = nowUs;
    latestImuWzRadS = 0.0f;
    haveImuYawRateReference = true;
    haveImuYawRateSample = false;
    return;
  }

  float dtSec = (nowUs - lastYawRateUs) * 1.0e-6f;
  if (dtSec <= 0.001f) {
    return;
  }

  latestImuWzRadS = wrapPi(yawRad - lastYawRateYawRad) / dtSec;
  lastYawRateYawRad = yawRad;
  lastYawRateUs = nowUs;
  latestImuSampleMs = millis();
  haveImuYawRateSample = true;
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

uint32_t lastImuRetryMs = 0;

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
  if (!imuReady) {
    if (millis() - lastImuRetryMs >= 2000) {
      lastImuRetryMs = millis();
      if (bno08x.begin_I2C(BNO08x_I2CADDR_DEFAULT, &Wire) || bno08x.begin_I2C(0x4B, &Wire)) {
        imuReady = enableRotationVector();
        if (imuReady) {
          Serial.println("OK IMU READY");
          if (imuRequested && !imuStreaming) {
            imuStreaming = true;
            nextImuPrintMs = millis();
            Serial.println("OK IMU ON");
          }
        }
      } else {
        Serial.println("WARN IMU not found");
      }
    }
    return;
  }

  if (bno08x.wasReset()) {
    enableRotationVector();
    resetImuYawRateEstimator();
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
    updateImuYawRate(latestYawRad);
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

void handleServoCommand(char *&cursor) {
  char *mode = strtok_r(cursor, " ", &cursor);
  if (mode == nullptr) {
    Serial.println("ERR SERVO needs: LEFT <deg> | RIGHT <deg> | BOTH <left_deg> <right_deg> | TEST");
    return;
  }
  uppercaseToken(mode);

  if (strcmp(mode, "LEFT") == 0) {
    bool ok = true;
    int degrees = readIntToken(cursor, ok);
    if (!ok) {
      Serial.println("ERR SERVO LEFT needs degree 0..180");
      return;
    }
    degrees = constrain(degrees, 0, 180);
    writeServoAngle(leftGateServo, degrees);
    Serial.print("OK SERVO LEFT ");
    Serial.println(degrees);
    return;
  }

  if (strcmp(mode, "RIGHT") == 0) {
    bool ok = true;
    int degrees = readIntToken(cursor, ok);
    if (!ok) {
      Serial.println("ERR SERVO RIGHT needs degree 0..180");
      return;
    }
    degrees = constrain(degrees, 0, 180);
    writeServoAngle(rightGateServo, degrees);
    Serial.print("OK SERVO RIGHT ");
    Serial.println(degrees);
    return;
  }

  if (strcmp(mode, "BOTH") == 0) {
    bool ok = true;
    int leftDegrees = readIntToken(cursor, ok);
    int rightDegrees = readIntToken(cursor, ok);
    if (!ok) {
      Serial.println("ERR SERVO BOTH needs: BOTH <left_deg> <right_deg>");
      return;
    }
    leftDegrees = constrain(leftDegrees, 0, 180);
    rightDegrees = constrain(rightDegrees, 0, 180);
    writeServoAngle(leftGateServo, leftDegrees);
    writeServoAngle(rightGateServo, rightDegrees);
    Serial.print("OK SERVO BOTH L=");
    Serial.print(leftDegrees);
    Serial.print(" R=");
    Serial.println(rightDegrees);
    return;
  }

  if (strcmp(mode, "TEST") == 0) {
    Serial.println("OK SERVO TEST close -> open -> center -> close");
    closeGate();
    holdServos(700);
    openGate();
    holdServos(700);
    writeServoAngle(leftGateServo, 90);
    writeServoAngle(rightGateServo, 90);
    Serial.println("OK SERVO BOTH L=90 R=90");
    holdServos(700);
    closeGate();
    return;
  }

  Serial.println("ERR SERVO needs: LEFT <deg> | RIGHT <deg> | BOTH <left_deg> <right_deg> | TEST");
}

void setSingleMotorTarget(int motorIndex, int pwm) {
  int values[MOTOR_COUNT] = {0, 0, 0, 0};
  values[motorIndex] = clampPwm(pwm);
  setAllTargets(values[0], values[1], values[2], values[3]);
}

void serviceRobotFor(uint32_t durationMs) {
  uint32_t startMs = millis();
  while ((uint32_t)(millis() - startMs) < durationMs) {
    updateMotorRamp();
    updateServos();
    updateImu();
    updateIrSensor();
    delay(1);
  }
}

void printEncoderTestResult(const char *motorName, int32_t *ticks) {
  Serial.print("ENC_TEST motor=");
  Serial.print(motorName);
  for (int i = 0; i < MOTOR_COUNT; i++) {
    Serial.print(' ');
    Serial.print(motors[i].name);
    Serial.print('=');
    Serial.print(ticks[i]);
  }
  Serial.println();
}

void runEncoderMappingTest(int basePwm, int durationMs) {
  basePwm = clampPwm(basePwm);
  if (basePwm == 0 || durationMs <= 0) {
    Serial.println("ERR ENC TEST needs nonzero base and positive duration_ms");
    return;
  }

  Serial.println("OK ENC TEST");
  for (int i = 0; i < MOTOR_COUNT; i++) {
    forceStopAllMotors();
    serviceRobotFor(250);
    resetEncoderTicks();
    setSingleMotorTarget(i, basePwm);
    serviceRobotFor((uint32_t)durationMs);
    forceStopAllMotors();
    serviceRobotFor(250);

    int32_t ticks[MOTOR_COUNT];
    readEncoderTicks(ticks);
    printEncoderTestResult(motors[i].name, ticks);
  }
  resetEncoderTicks();
  Serial.println("OK ENC TEST DONE");
}

void handleEncoderCommand(char *&cursor) {
  char *mode = strtok_r(cursor, " ", &cursor);
  if (mode == nullptr || strcmp(mode, "?") == 0) {
    printEncoderStatus();
    return;
  }

  uppercaseToken(mode);
  if (strcmp(mode, "RESET") == 0) {
    resetEncoderTicks();
    Serial.println("OK ENC RESET");
    printEncoderStatus();
    return;
  }

  if (strcmp(mode, "ON") == 0) {
    encoderStreaming = true;
    nextEncoderPrintMs = millis();
    Serial.println("OK ENC ON");
    return;
  }

  if (strcmp(mode, "OFF") == 0) {
    encoderStreaming = false;
    Serial.println("OK ENC OFF");
    return;
  }

  if (strcmp(mode, "TEST") == 0) {
    bool ok = true;
    int base = readIntToken(cursor, ok);
    int durationMs = readIntToken(cursor, ok);
    if (!ok) {
      Serial.println("ERR ENC TEST needs: ENC TEST <base> <duration_ms>");
      return;
    }
    runEncoderMappingTest(base, durationMs);
    return;
  }

  Serial.println("ERR ENC needs: ENC? | ENC RESET | ENC ON | ENC OFF | ENC TEST <base> <duration_ms>");
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
    straightRunActive = false;
    startSetClosedLoop(fl, fr, bl, br);
    return;
  }

  if (strcmp(command, "SET1") == 0) {
    bool ok = true;
    float fl = readFloatToken(cursor, ok);
    float fr = readFloatToken(cursor, ok);
    float bl = readFloatToken(cursor, ok);
    float br = readFloatToken(cursor, ok);
    if (!ok) {
      Serial.println("ERR SET1 needs: SET1 <fl_cps> <fr_cps> <bl_cps> <br_cps>");
      return;
    }

    startSet1VelocityClosedLoop(fl, fr, bl, br);
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

    resetSetPwmControlState();
    resetSet1VelocityControlState();
    int fl, fr, bl, br;
    computeScaledWheelPwm(base, flScale, frScale, blScale, brScale, fl, fr, bl, br);
    straightRunActive = false;
    setAllTargets(fl, fr, bl, br);

    timedRunActive = strcmp(command, "RUN") == 0;
    timedRunStopAtMs = millis() + (uint32_t)durationMs;
    Serial.println(timedRunActive ? "OK RUN" : "OK DRIVE");
    printStatus();
    return;
  }

  if (strcmp(command, "STRAIGHT") == 0) {
    bool ok = true;
    int base = readIntToken(cursor, ok);
    int durationMs = readIntToken(cursor, ok);
    if (!ok) {
      Serial.println("ERR STRAIGHT needs: STRAIGHT <base> <duration_ms>");
      return;
    }

    resetSetPwmControlState();
    resetSet1VelocityControlState();
    startStraightRun(base, durationMs);
    return;
  }

  if (strcmp(command, "ENC?") == 0) {
    printEncoderStatus();
    return;
  }

  if (strcmp(command, "ENC") == 0) {
    handleEncoderCommand(cursor);
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
      imuRequested = true;
      imuStreaming = imuReady;
      nextImuPrintMs = millis();
      Serial.println(imuReady ? "OK IMU ON" : "ERR IMU not ready");
      return;
    }
    if (strcmp(mode, "OFF") == 0) {
      imuRequested = false;
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
      resetImuYawRateEstimator();
    }
    Serial.println("OK ZERO_YAW");
    return;
  }

  if (strcmp(command, "GATE") == 0) {
    handleGateCommand(cursor);
    return;
  }

  if (strcmp(command, "SERVO") == 0) {
    handleServoCommand(cursor);
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
    Serial.println("Commands: PING | STOP | SET <fl> <fr> <bl> <br> (fixed+PI) | SET1 <fl_cps> <fr_cps> <bl_cps> <br_cps> | DRIVE <base> <fl_s> <fr_s> <bl_s> <br_s> | RUN <base> <fl_s> <fr_s> <bl_s> <br_s> <ms> | STRAIGHT <base> <ms> | ENC? | ENC RESET | ENC ON|OFF | ENC TEST <base> <ms> | IMU ON|OFF | ZERO_YAW | GATE OPEN|CLOSE|? | SERVO LEFT <deg> | SERVO RIGHT <deg> | SERVO BOTH <left_deg> <right_deg> | SERVO TEST | CARGO? | CARGO RESET | BATCH <0|1|2> | CAPACITY <1..3> | AUTO_GATE ON|OFF | UNLOAD");
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
  setupEncoders();

  pinMode(LEFT_GATE_SERVO_PIN, OUTPUT);
  pinMode(RIGHT_GATE_SERVO_PIN, OUTPUT);
  digitalWrite(LEFT_GATE_SERVO_PIN, LOW);
  digitalWrite(RIGHT_GATE_SERVO_PIN, LOW);
  closeGate();
  holdServos(500);

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
  updateSet1VelocityClosedLoop();
  updateSetClosedLoop();
  updateStraightRun();
  updateMotorRamp();
  updateServos();
  updateImu();
  updateIrSensor();
  updateEncoderStreaming();

  if (timedRunActive && (int32_t)(millis() - timedRunStopAtMs) >= 0) {
    forceStopAllMotors();
    Serial.println("OK DONE");
  }
}
