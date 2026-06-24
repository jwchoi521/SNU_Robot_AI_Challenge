/*
  ESP32 motor and encoder bridge for SNU Robot AI Challenge.

  Serial protocol:
    Jetson -> ESP32: M <front_left> <front_right> <rear_left> <rear_right>
      Values are normalized motor powers in the range -1.0..1.0.

    Jetson -> ESP32: V <front_left> <front_right> <rear_left> <rear_right>
      Values are normalized wheel speed targets in the range -1.0..1.0.
      ESP32 uses encoder feedback to regulate each wheel speed.

    ESP32 -> Jetson: E <front_left_count> <front_right_count> <rear_left_count> <rear_right_count>
      Counts are raw quadrature transition counts.
*/

#include <Arduino.h>

struct MotorPins {
  int pin_a;
  int pin_b;
  float sign;
};

struct EncoderPins {
  int pin_a;
  int pin_b;
  float sign;
};

constexpr int PWM_FREQUENCY_HZ = 1000;
constexpr int PWM_RESOLUTION_BITS = 10;
constexpr int PWM_MAX = (1 << PWM_RESOLUTION_BITS) - 1;
constexpr unsigned long COMMAND_TIMEOUT_MS = 500;
constexpr unsigned long ENCODER_REPORT_PERIOD_MS = 50;
constexpr unsigned long CONTROL_PERIOD_MS = 20;

// Closed-loop velocity controller. These values are intentionally conservative
// and should be tuned on the lifted robot before floor driving.
constexpr float MAX_TARGET_COUNTS_PER_SEC = 1200.0f;
constexpr float VELOCITY_FEED_FORWARD = 0.35f;
constexpr float VELOCITY_KP = 0.0005f;
constexpr float VELOCITY_KI = 0.00008f;
constexpr float VELOCITY_INTEGRAL_LIMIT = 2500.0f;
constexpr float MIN_MOVING_POWER = 0.12f;

// Motor input pins from the current wiring note.
MotorPins FRONT_LEFT_MOTOR = {23, 25, -1.0f};
MotorPins FRONT_RIGHT_MOTOR = {4, 5, 1.0f};
MotorPins REAR_LEFT_MOTOR = {2, 15, -1.0f};
MotorPins REAR_RIGHT_MOTOR = {14, 13, 1.0f};

// Encoder pins from the current wiring note.
EncoderPins FRONT_LEFT_ENCODER = {18, 19, 1.0f};
EncoderPins FRONT_RIGHT_ENCODER = {16, 17, 1.0f};
EncoderPins REAR_LEFT_ENCODER = {32, 33, 1.0f};
EncoderPins REAR_RIGHT_ENCODER = {26, 27, 1.0f};

volatile long front_left_count = 0;
volatile long front_right_count = 0;
volatile long rear_left_count = 0;
volatile long rear_right_count = 0;

volatile uint8_t front_left_state = 0;
volatile uint8_t front_right_state = 0;
volatile uint8_t rear_left_state = 0;
volatile uint8_t rear_right_state = 0;

unsigned long last_command_ms = 0;
unsigned long last_encoder_report_ms = 0;
unsigned long last_control_ms = 0;

bool closed_loop_enabled = false;
float front_left_target_cps = 0.0f;
float front_right_target_cps = 0.0f;
float rear_left_target_cps = 0.0f;
float rear_right_target_cps = 0.0f;

long front_left_control_count = 0;
long front_right_control_count = 0;
long rear_left_control_count = 0;
long rear_right_control_count = 0;

float front_left_integral = 0.0f;
float front_right_integral = 0.0f;
float rear_left_integral = 0.0f;
float rear_right_integral = 0.0f;

uint8_t readEncoderState(const EncoderPins& encoder) {
  const uint8_t a = digitalRead(encoder.pin_a) ? 1 : 0;
  const uint8_t b = digitalRead(encoder.pin_b) ? 1 : 0;
  return (a << 1) | b;
}

int transitionDelta(uint8_t previous, uint8_t current) {
  if ((previous == 0b00 && current == 0b01) ||
      (previous == 0b01 && current == 0b11) ||
      (previous == 0b11 && current == 0b10) ||
      (previous == 0b10 && current == 0b00)) {
    return 1;
  }
  if ((previous == 0b00 && current == 0b10) ||
      (previous == 0b10 && current == 0b11) ||
      (previous == 0b11 && current == 0b01) ||
      (previous == 0b01 && current == 0b00)) {
    return -1;
  }
  return 0;
}

void updateEncoder(
  const EncoderPins& encoder,
  volatile uint8_t& previous_state,
  volatile long& count
) {
  const uint8_t current = readEncoderState(encoder);
  const int delta = transitionDelta(previous_state, current);
  count += static_cast<long>(delta * encoder.sign);
  previous_state = current;
}

void IRAM_ATTR frontLeftEncoderIsr() {
  updateEncoder(FRONT_LEFT_ENCODER, front_left_state, front_left_count);
}

void IRAM_ATTR frontRightEncoderIsr() {
  updateEncoder(FRONT_RIGHT_ENCODER, front_right_state, front_right_count);
}

void IRAM_ATTR rearLeftEncoderIsr() {
  updateEncoder(REAR_LEFT_ENCODER, rear_left_state, rear_left_count);
}

void IRAM_ATTR rearRightEncoderIsr() {
  updateEncoder(REAR_RIGHT_ENCODER, rear_right_state, rear_right_count);
}

void setupMotor(const MotorPins& motor) {
  ledcAttach(motor.pin_a, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcAttach(motor.pin_b, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcWrite(motor.pin_a, 0);
  ledcWrite(motor.pin_b, 0);
}

void setupEncoder(const EncoderPins& encoder, void (*isr)(), volatile uint8_t& state) {
  pinMode(encoder.pin_a, INPUT_PULLUP);
  pinMode(encoder.pin_b, INPUT_PULLUP);
  state = readEncoderState(encoder);
  attachInterrupt(digitalPinToInterrupt(encoder.pin_a), isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoder.pin_b), isr, CHANGE);
}

void setMotor(const MotorPins& motor, float power) {
  float signed_power = power * motor.sign;
  signed_power = constrain(signed_power, -1.0f, 1.0f);
  const int duty = static_cast<int>(abs(signed_power) * PWM_MAX);

  if (signed_power >= 0.0f) {
    ledcWrite(motor.pin_a, duty);
    ledcWrite(motor.pin_b, 0);
  } else {
    ledcWrite(motor.pin_a, 0);
    ledcWrite(motor.pin_b, duty);
  }
}

void stopAllMotors() {
  setMotor(FRONT_LEFT_MOTOR, 0.0f);
  setMotor(FRONT_RIGHT_MOTOR, 0.0f);
  setMotor(REAR_LEFT_MOTOR, 0.0f);
  setMotor(REAR_RIGHT_MOTOR, 0.0f);
}

void resetClosedLoopState() {
  front_left_target_cps = 0.0f;
  front_right_target_cps = 0.0f;
  rear_left_target_cps = 0.0f;
  rear_right_target_cps = 0.0f;
  front_left_integral = 0.0f;
  front_right_integral = 0.0f;
  rear_left_integral = 0.0f;
  rear_right_integral = 0.0f;

  noInterrupts();
  front_left_control_count = front_left_count;
  front_right_control_count = front_right_count;
  rear_left_control_count = rear_left_count;
  rear_right_control_count = rear_right_count;
  interrupts();

  last_control_ms = millis();
}

float normalizedToCountsPerSec(float value) {
  return constrain(value, -1.0f, 1.0f) * MAX_TARGET_COUNTS_PER_SEC;
}

float updateWheelController(
  float target_cps,
  float measured_cps,
  float dt_sec,
  float& integral
) {
  if (fabsf(target_cps) < 1.0f) {
    integral = 0.0f;
    return 0.0f;
  }

  const float target_norm = constrain(
    target_cps / MAX_TARGET_COUNTS_PER_SEC,
    -1.0f,
    1.0f
  );
  const float error = target_cps - measured_cps;
  integral = constrain(
    integral + error * dt_sec,
    -VELOCITY_INTEGRAL_LIMIT,
    VELOCITY_INTEGRAL_LIMIT
  );

  float power = target_norm * VELOCITY_FEED_FORWARD +
                VELOCITY_KP * error +
                VELOCITY_KI * integral;
  const float power_limit = constrain(fabsf(target_norm), MIN_MOVING_POWER, 1.0f);

  if (target_cps > 0.0f) {
    power = constrain(power, 0.0f, power_limit);
    if (power > 0.0f && power < MIN_MOVING_POWER) {
      power = MIN_MOVING_POWER;
    }
  } else {
    power = constrain(power, -power_limit, 0.0f);
    if (power < 0.0f && power > -MIN_MOVING_POWER) {
      power = -MIN_MOVING_POWER;
    }
  }
  return power;
}

void runClosedLoopControl(unsigned long now) {
  if (!closed_loop_enabled) {
    return;
  }
  if (now - last_control_ms < CONTROL_PERIOD_MS) {
    return;
  }

  noInterrupts();
  const long fl_count = front_left_count;
  const long fr_count = front_right_count;
  const long rl_count = rear_left_count;
  const long rr_count = rear_right_count;
  interrupts();

  const float dt_sec = max(0.001f, (now - last_control_ms) / 1000.0f);
  const float fl_cps = (fl_count - front_left_control_count) / dt_sec;
  const float fr_cps = (fr_count - front_right_control_count) / dt_sec;
  const float rl_cps = (rl_count - rear_left_control_count) / dt_sec;
  const float rr_cps = (rr_count - rear_right_control_count) / dt_sec;

  front_left_control_count = fl_count;
  front_right_control_count = fr_count;
  rear_left_control_count = rl_count;
  rear_right_control_count = rr_count;
  last_control_ms = now;

  setMotor(
    FRONT_LEFT_MOTOR,
    updateWheelController(
      front_left_target_cps,
      fl_cps,
      dt_sec,
      front_left_integral
    )
  );
  setMotor(
    FRONT_RIGHT_MOTOR,
    updateWheelController(
      front_right_target_cps,
      fr_cps,
      dt_sec,
      front_right_integral
    )
  );
  setMotor(
    REAR_LEFT_MOTOR,
    updateWheelController(
      rear_left_target_cps,
      rl_cps,
      dt_sec,
      rear_left_integral
    )
  );
  setMotor(
    REAR_RIGHT_MOTOR,
    updateWheelController(
      rear_right_target_cps,
      rr_cps,
      dt_sec,
      rear_right_integral
    )
  );
}

void handleMotorCommand(const String& line) {
  float front_left = 0.0f;
  float front_right = 0.0f;
  float rear_left = 0.0f;
  float rear_right = 0.0f;

  const int parsed = sscanf(
    line.c_str(),
    "M %f %f %f %f",
    &front_left,
    &front_right,
    &rear_left,
    &rear_right
  );
  if (parsed != 4) {
    Serial.println("ERR invalid_motor_command");
    return;
  }

  closed_loop_enabled = false;
  resetClosedLoopState();
  setMotor(FRONT_LEFT_MOTOR, front_left);
  setMotor(FRONT_RIGHT_MOTOR, front_right);
  setMotor(REAR_LEFT_MOTOR, rear_left);
  setMotor(REAR_RIGHT_MOTOR, rear_right);
  last_command_ms = millis();
  Serial.println("OK");
}

void handleVelocityCommand(const String& line) {
  float front_left = 0.0f;
  float front_right = 0.0f;
  float rear_left = 0.0f;
  float rear_right = 0.0f;

  const int parsed = sscanf(
    line.c_str(),
    "V %f %f %f %f",
    &front_left,
    &front_right,
    &rear_left,
    &rear_right
  );
  if (parsed != 4) {
    Serial.println("ERR invalid_velocity_command");
    return;
  }

  front_left_target_cps = normalizedToCountsPerSec(front_left);
  front_right_target_cps = normalizedToCountsPerSec(front_right);
  rear_left_target_cps = normalizedToCountsPerSec(rear_left);
  rear_right_target_cps = normalizedToCountsPerSec(rear_right);
  closed_loop_enabled = true;
  last_command_ms = millis();
  Serial.println("OK");
}

void handleSerial() {
  while (Serial.available() > 0) {
    const String line = Serial.readStringUntil('\n');
    if (line.length() == 0) {
      continue;
    }
    if (line[0] == 'M') {
      handleMotorCommand(line);
    } else if (line[0] == 'V') {
      handleVelocityCommand(line);
    }
  }
}

void reportEncoders() {
  noInterrupts();
  const long fl = front_left_count;
  const long fr = front_right_count;
  const long rl = rear_left_count;
  const long rr = rear_right_count;
  interrupts();

  Serial.print("E ");
  Serial.print(fl);
  Serial.print(' ');
  Serial.print(fr);
  Serial.print(' ');
  Serial.print(rl);
  Serial.print(' ');
  Serial.println(rr);
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(5);

  setupMotor(FRONT_LEFT_MOTOR);
  setupMotor(FRONT_RIGHT_MOTOR);
  setupMotor(REAR_LEFT_MOTOR);
  setupMotor(REAR_RIGHT_MOTOR);
  stopAllMotors();

  setupEncoder(FRONT_LEFT_ENCODER, frontLeftEncoderIsr, front_left_state);
  setupEncoder(FRONT_RIGHT_ENCODER, frontRightEncoderIsr, front_right_state);
  setupEncoder(REAR_LEFT_ENCODER, rearLeftEncoderIsr, rear_left_state);
  setupEncoder(REAR_RIGHT_ENCODER, rearRightEncoderIsr, rear_right_state);

  resetClosedLoopState();
  last_command_ms = millis();
  last_encoder_report_ms = millis();
  Serial.println("READY esp32_motor_bridge");
}

void loop() {
  handleSerial();

  const unsigned long now = millis();
  if (now - last_command_ms > COMMAND_TIMEOUT_MS) {
    if (closed_loop_enabled) {
      closed_loop_enabled = false;
      resetClosedLoopState();
    }
    stopAllMotors();
  } else {
    runClosedLoopControl(now);
  }
  if (now - last_encoder_report_ms >= ENCODER_REPORT_PERIOD_MS) {
    reportEncoders();
    last_encoder_report_ms = now;
  }
}
