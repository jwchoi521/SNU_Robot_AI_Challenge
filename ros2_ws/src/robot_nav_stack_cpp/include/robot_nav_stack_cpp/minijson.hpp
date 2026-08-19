#pragma once

#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace robot_nav_stack_cpp::minijson
{

class Value
{
public:
  enum class Type { Null, Boolean, Number, String, Object, Array };
  using Object = std::map<std::string, Value>;
  using Array = std::vector<Value>;

  Value() = default;
  explicit Value(bool value) : type_(Type::Boolean), boolean_(value) {}
  explicit Value(double value) : type_(Type::Number), number_(value) {}
  explicit Value(std::string value) : type_(Type::String), string_(std::move(value)) {}
  explicit Value(Object value) : type_(Type::Object), object_(std::move(value)) {}
  explicit Value(Array value) : type_(Type::Array), array_(std::move(value)) {}

  Type type() const {return type_;}
  bool is_null() const {return type_ == Type::Null;}
  bool is_bool() const {return type_ == Type::Boolean;}
  bool is_number() const {return type_ == Type::Number;}
  bool is_string() const {return type_ == Type::String;}
  bool is_object() const {return type_ == Type::Object;}
  bool is_array() const {return type_ == Type::Array;}

  bool as_bool() const
  {
    if (!is_bool()) {throw std::runtime_error("JSON value is not boolean");}
    return boolean_;
  }

  double as_double() const
  {
    if (is_number()) {return number_;}
    if (is_string()) {
      std::size_t parsed = 0;
      const double result = std::stod(string_, &parsed);
      if (parsed != string_.size()) {throw std::runtime_error("invalid numeric string");}
      return result;
    }
    throw std::runtime_error("JSON value is not numeric");
  }

  int as_int() const
  {
    if (is_number()) {return static_cast<int>(number_);}
    if (is_string()) {
      std::size_t parsed = 0;
      const int result = std::stoi(string_, &parsed);
      if (parsed != string_.size()) {throw std::runtime_error("invalid integer string");}
      return result;
    }
    throw std::runtime_error("JSON value is not an integer");
  }

  std::string as_string() const
  {
    if (is_string()) {return string_;}
    if (is_number()) {return std::to_string(number_);}
    if (is_bool()) {return boolean_ ? "True" : "False";}
    if (is_null()) {return "None";}
    throw std::runtime_error("JSON object/array cannot be converted to string");
  }

  const Object & as_object() const
  {
    if (!is_object()) {throw std::runtime_error("JSON value is not an object");}
    return object_;
  }

  const Array & as_array() const
  {
    if (!is_array()) {throw std::runtime_error("JSON value is not an array");}
    return array_;
  }

  const Value & at(const std::string & key) const
  {
    const auto & object = as_object();
    const auto found = object.find(key);
    if (found == object.end()) {throw std::runtime_error("missing JSON key: " + key);}
    return found->second;
  }

  const Value * find(const std::string & key) const
  {
    if (!is_object()) {return nullptr;}
    const auto found = object_.find(key);
    return found == object_.end() ? nullptr : &found->second;
  }

private:
  Type type_{Type::Null};
  bool boolean_{false};
  double number_{0.0};
  std::string string_;
  Object object_;
  Array array_;
};

class Parser
{
public:
  explicit Parser(const std::string & text) : text_(text) {}

  Value parse()
  {
    skip_space();
    Value value = parse_value();
    skip_space();
    if (position_ != text_.size()) {fail("trailing data");}
    return value;
  }

private:
  [[noreturn]] void fail(const std::string & message) const
  {
    throw std::runtime_error(
            "invalid JSON at byte " + std::to_string(position_) + ": " + message);
  }

  void skip_space()
  {
    while (position_ < text_.size() &&
      std::isspace(static_cast<unsigned char>(text_[position_])))
    {
      ++position_;
    }
  }

  bool consume(char expected)
  {
    if (position_ < text_.size() && text_[position_] == expected) {
      ++position_;
      return true;
    }
    return false;
  }

  void expect(char expected)
  {
    if (!consume(expected)) {fail(std::string("expected '") + expected + "'");}
  }

  Value parse_value()
  {
    if (position_ >= text_.size()) {fail("unexpected end of input");}
    switch (text_[position_]) {
      case 'n': parse_literal("null"); return Value();
      case 't': parse_literal("true"); return Value(true);
      case 'f': parse_literal("false"); return Value(false);
      case '"': return Value(parse_string());
      case '{': return Value(parse_object());
      case '[': return Value(parse_array());
      default:
        if (text_[position_] == '-' || std::isdigit(static_cast<unsigned char>(text_[position_]))) {
          return Value(parse_number());
        }
        fail("unexpected token");
    }
  }

  void parse_literal(const char * literal)
  {
    const std::string value(literal);
    if (text_.compare(position_, value.size(), value) != 0) {fail("invalid literal");}
    position_ += value.size();
  }

  static void append_utf8(std::string & output, std::uint32_t codepoint)
  {
    if (codepoint <= 0x7FU) {
      output.push_back(static_cast<char>(codepoint));
    } else if (codepoint <= 0x7FFU) {
      output.push_back(static_cast<char>(0xC0U | (codepoint >> 6U)));
      output.push_back(static_cast<char>(0x80U | (codepoint & 0x3FU)));
    } else {
      output.push_back(static_cast<char>(0xE0U | (codepoint >> 12U)));
      output.push_back(static_cast<char>(0x80U | ((codepoint >> 6U) & 0x3FU)));
      output.push_back(static_cast<char>(0x80U | (codepoint & 0x3FU)));
    }
  }

  std::string parse_string()
  {
    expect('"');
    std::string output;
    while (position_ < text_.size()) {
      const char ch = text_[position_++];
      if (ch == '"') {return output;}
      if (static_cast<unsigned char>(ch) < 0x20U) {fail("control character in string");}
      if (ch != '\\') {
        output.push_back(ch);
        continue;
      }
      if (position_ >= text_.size()) {fail("unfinished escape");}
      const char escaped = text_[position_++];
      switch (escaped) {
        case '"': output.push_back('"'); break;
        case '\\': output.push_back('\\'); break;
        case '/': output.push_back('/'); break;
        case 'b': output.push_back('\b'); break;
        case 'f': output.push_back('\f'); break;
        case 'n': output.push_back('\n'); break;
        case 'r': output.push_back('\r'); break;
        case 't': output.push_back('\t'); break;
        case 'u': {
          if (position_ + 4U > text_.size()) {fail("short unicode escape");}
          std::uint32_t codepoint = 0U;
          for (int index = 0; index < 4; ++index) {
            const char digit = text_[position_++];
            codepoint <<= 4U;
            if (digit >= '0' && digit <= '9') {codepoint += digit - '0';}
            else if (digit >= 'a' && digit <= 'f') {codepoint += digit - 'a' + 10;}
            else if (digit >= 'A' && digit <= 'F') {codepoint += digit - 'A' + 10;}
            else {fail("invalid unicode escape");}
          }
          append_utf8(output, codepoint);
          break;
        }
        default: fail("invalid escape");
      }
    }
    fail("unterminated string");
  }

  double parse_number()
  {
    const std::size_t start = position_;
    if (consume('-')) {}
    if (consume('0')) {
      // A leading zero is complete unless followed by a fraction/exponent.
    } else {
      if (position_ >= text_.size() ||
        !std::isdigit(static_cast<unsigned char>(text_[position_])))
      {
        fail("invalid number");
      }
      while (position_ < text_.size() &&
        std::isdigit(static_cast<unsigned char>(text_[position_])))
      {
        ++position_;
      }
    }
    if (consume('.')) {
      if (position_ >= text_.size() ||
        !std::isdigit(static_cast<unsigned char>(text_[position_])))
      {
        fail("invalid fraction");
      }
      while (position_ < text_.size() &&
        std::isdigit(static_cast<unsigned char>(text_[position_])))
      {
        ++position_;
      }
    }
    if (position_ < text_.size() && (text_[position_] == 'e' || text_[position_] == 'E')) {
      ++position_;
      if (position_ < text_.size() && (text_[position_] == '+' || text_[position_] == '-')) {
        ++position_;
      }
      if (position_ >= text_.size() ||
        !std::isdigit(static_cast<unsigned char>(text_[position_])))
      {
        fail("invalid exponent");
      }
      while (position_ < text_.size() &&
        std::isdigit(static_cast<unsigned char>(text_[position_])))
      {
        ++position_;
      }
    }
    const std::string token = text_.substr(start, position_ - start);
    char * end = nullptr;
    const double value = std::strtod(token.c_str(), &end);
    if (end != token.c_str() + token.size()) {fail("invalid number");}
    return value;
  }

  Value::Object parse_object()
  {
    expect('{');
    skip_space();
    Value::Object object;
    if (consume('}')) {return object;}
    while (true) {
      skip_space();
      if (position_ >= text_.size() || text_[position_] != '"') {
        fail("object key must be a string");
      }
      const std::string key = parse_string();
      skip_space();
      expect(':');
      skip_space();
      object[key] = parse_value();
      skip_space();
      if (consume('}')) {return object;}
      expect(',');
      skip_space();
    }
  }

  Value::Array parse_array()
  {
    expect('[');
    skip_space();
    Value::Array array;
    if (consume(']')) {return array;}
    while (true) {
      array.push_back(parse_value());
      skip_space();
      if (consume(']')) {return array;}
      expect(',');
      skip_space();
    }
  }

  const std::string & text_;
  std::size_t position_{0U};
};

inline Value parse(const std::string & text) {return Parser(text).parse();}

}  // namespace robot_nav_stack_cpp::minijson
