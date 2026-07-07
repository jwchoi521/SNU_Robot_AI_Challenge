#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "robot_object_detector_ros__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__robot_object_detector_ros__msg__Detection2D() -> *const std::ffi::c_void;
}

#[link(name = "robot_object_detector_ros__rosidl_generator_c")]
extern "C" {
    fn robot_object_detector_ros__msg__Detection2D__init(msg: *mut Detection2D) -> bool;
    fn robot_object_detector_ros__msg__Detection2D__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Detection2D>, size: usize) -> bool;
    fn robot_object_detector_ros__msg__Detection2D__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Detection2D>);
    fn robot_object_detector_ros__msg__Detection2D__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Detection2D>, out_seq: *mut rosidl_runtime_rs::Sequence<Detection2D>) -> bool;
}

// Corresponds to robot_object_detector_ros__msg__Detection2D
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection2D {

    // This member is not documented.
    #[allow(missing_docs)]
    pub class_id: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub class_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub x1: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y1: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub x2: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y2: f32,

}



impl Default for Detection2D {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !robot_object_detector_ros__msg__Detection2D__init(&mut msg as *mut _) {
        panic!("Call to robot_object_detector_ros__msg__Detection2D__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Detection2D {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__Detection2D__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__Detection2D__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__Detection2D__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Detection2D {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Detection2D where Self: Sized {
  const TYPE_NAME: &'static str = "robot_object_detector_ros/msg/Detection2D";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__robot_object_detector_ros__msg__Detection2D() }
  }
}


#[link(name = "robot_object_detector_ros__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__robot_object_detector_ros__msg__Detection2DArray() -> *const std::ffi::c_void;
}

#[link(name = "robot_object_detector_ros__rosidl_generator_c")]
extern "C" {
    fn robot_object_detector_ros__msg__Detection2DArray__init(msg: *mut Detection2DArray) -> bool;
    fn robot_object_detector_ros__msg__Detection2DArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Detection2DArray>, size: usize) -> bool;
    fn robot_object_detector_ros__msg__Detection2DArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Detection2DArray>);
    fn robot_object_detector_ros__msg__Detection2DArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Detection2DArray>, out_seq: *mut rosidl_runtime_rs::Sequence<Detection2DArray>) -> bool;
}

// Corresponds to robot_object_detector_ros__msg__Detection2DArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection2DArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub detections: rosidl_runtime_rs::Sequence<super::super::msg::rmw::Detection2D>,

}



impl Default for Detection2DArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !robot_object_detector_ros__msg__Detection2DArray__init(&mut msg as *mut _) {
        panic!("Call to robot_object_detector_ros__msg__Detection2DArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Detection2DArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__Detection2DArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__Detection2DArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__Detection2DArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Detection2DArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Detection2DArray where Self: Sized {
  const TYPE_NAME: &'static str = "robot_object_detector_ros/msg/Detection2DArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__robot_object_detector_ros__msg__Detection2DArray() }
  }
}


#[link(name = "robot_object_detector_ros__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__robot_object_detector_ros__msg__FruitClassification() -> *const std::ffi::c_void;
}

#[link(name = "robot_object_detector_ros__rosidl_generator_c")]
extern "C" {
    fn robot_object_detector_ros__msg__FruitClassification__init(msg: *mut FruitClassification) -> bool;
    fn robot_object_detector_ros__msg__FruitClassification__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FruitClassification>, size: usize) -> bool;
    fn robot_object_detector_ros__msg__FruitClassification__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FruitClassification>);
    fn robot_object_detector_ros__msg__FruitClassification__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FruitClassification>, out_seq: *mut rosidl_runtime_rs::Sequence<FruitClassification>) -> bool;
}

// Corresponds to robot_object_detector_ros__msg__FruitClassification
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FruitClassification {

    // This member is not documented.
    #[allow(missing_docs)]
    pub cube: super::super::msg::rmw::Detection2D,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fruit_kind: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pick_allowed: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub class_names: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub probabilities: rosidl_runtime_rs::Sequence<f32>,

}



impl Default for FruitClassification {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !robot_object_detector_ros__msg__FruitClassification__init(&mut msg as *mut _) {
        panic!("Call to robot_object_detector_ros__msg__FruitClassification__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FruitClassification {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__FruitClassification__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__FruitClassification__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__FruitClassification__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FruitClassification {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FruitClassification where Self: Sized {
  const TYPE_NAME: &'static str = "robot_object_detector_ros/msg/FruitClassification";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__robot_object_detector_ros__msg__FruitClassification() }
  }
}


#[link(name = "robot_object_detector_ros__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__robot_object_detector_ros__msg__FruitClassificationArray() -> *const std::ffi::c_void;
}

#[link(name = "robot_object_detector_ros__rosidl_generator_c")]
extern "C" {
    fn robot_object_detector_ros__msg__FruitClassificationArray__init(msg: *mut FruitClassificationArray) -> bool;
    fn robot_object_detector_ros__msg__FruitClassificationArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FruitClassificationArray>, size: usize) -> bool;
    fn robot_object_detector_ros__msg__FruitClassificationArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FruitClassificationArray>);
    fn robot_object_detector_ros__msg__FruitClassificationArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FruitClassificationArray>, out_seq: *mut rosidl_runtime_rs::Sequence<FruitClassificationArray>) -> bool;
}

// Corresponds to robot_object_detector_ros__msg__FruitClassificationArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FruitClassificationArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub classifications: rosidl_runtime_rs::Sequence<super::super::msg::rmw::FruitClassification>,

}



impl Default for FruitClassificationArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !robot_object_detector_ros__msg__FruitClassificationArray__init(&mut msg as *mut _) {
        panic!("Call to robot_object_detector_ros__msg__FruitClassificationArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FruitClassificationArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__FruitClassificationArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__FruitClassificationArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { robot_object_detector_ros__msg__FruitClassificationArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FruitClassificationArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FruitClassificationArray where Self: Sized {
  const TYPE_NAME: &'static str = "robot_object_detector_ros/msg/FruitClassificationArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__robot_object_detector_ros__msg__FruitClassificationArray() }
  }
}


