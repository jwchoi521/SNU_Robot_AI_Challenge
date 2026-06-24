/*
  ESP32 motor and encoder bridge for SNU Robot AI Challenge.

  Serial protocol:
    Jetson -> ESP32: M <front_left> <front_right> <rear_left> <rear_right>
      Values are normalized motor powers in the range -1.0..1.0.

    ESP32 -> Jetson: E <front_left_count> <front_right_count> <rear_left_count> <rear_right_count>
      Counts are raw quadrature transition counts.
*/

#include <Arduino.h>

struct MotorPins {
  int pin_a;
  int pin_b;
  int pwm_channel_a;
  int pwm_channel_b;
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

// Motor input pins from the current wiring note.
MotorPins FRONT_LEFT_MOTOR = {23, 25, 0, 1, 1.0f};
MotorPins FRONT_RIGHT_MOTOR = {4, 5, 2, 3, 1.0f};
MotorPins REAR_LEFT_MOTOR = {2, 15, 4, 5, 1.0f};
MotorPins REAR_RIGHT_MOTOR = {14, 13, 6, 7, 1.0f};

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
  ledcSetup(motor.pwm_channel_a, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcSetup(motor.pwm_channel_b, PWM_FREQUENCY_HZ, PWM_RESOLUTION_BITS);
  ledcAttachPin(motor.pin_a, motor.pwm_channel_a);
  ledcAttachPin(motor.pin_b, motor.pwm_channel_b);
  ledcWrite(motor.pwm_channel_a, 0);
  ledcWrite(motor.pwm_channel_b, 0);
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
    ledcWrite(motor.pwm_channel_a, duty);
    ledcWrite(motor.pwm_channel_b, 0);
  } else {
    ledcWrite(motor.pwm_channel_a, 0);
    ledcWrite(motor.pwm_channel_b, duty);
  }
}

void stopAllMotors() {
  setMotor(FRONT_LEFT_MOTOR, 0.0f);
  setMotor(FRONT_RIGHT_MOTOR, 0.0f);
  setMotor(REAR_LEFT_MOTOR, 0.0f);
  setMotor(REAR_RIGHT_MOTOR, 0.0f);
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

  setMotor(FRONT_LEFT_MOTOR, front_left);
  setMotor(FRONT_RIGHT_MOTOR, front_right);
  setMotor(REAR_LEFT_MOTOR, rear_left);
  setMotor(REAR_RIGHT_MOTOR, rear_right);
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

  last_command_ms = millis();
  last_encoder_report_ms = millis();
  Serial.println("READY esp32_motor_bridge");
}

void loop() {
  handleSerial();

  const unsigned long now = millis();
  if (now - last_command_ms > COMMAND_TIMEOUT_MS) {
    stopAllMotors();
  }
  if (now - last_encoder_report_ms >= ENCODER_REPORT_PERIOD_MS) {
    reportEncoders();
    last_encoder_report_ms = now;
  }
}
