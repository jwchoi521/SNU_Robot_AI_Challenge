#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "snu_robot_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__DetectedTarget() -> *const std::ffi::c_void;
}

#[link(name = "snu_robot_interfaces__rosidl_generator_c")]
extern "C" {
    fn snu_robot_interfaces__msg__DetectedTarget__init(msg: *mut DetectedTarget) -> bool;
    fn snu_robot_interfaces__msg__DetectedTarget__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DetectedTarget>, size: usize) -> bool;
    fn snu_robot_interfaces__msg__DetectedTarget__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DetectedTarget>);
    fn snu_robot_interfaces__msg__DetectedTarget__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DetectedTarget>, out_seq: *mut rosidl_runtime_rs::Sequence<DetectedTarget>) -> bool;
}

// Corresponds to snu_robot_interfaces__msg__DetectedTarget
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// One target produced by the camera detector and distance provider.
///
/// The current YOLO branch uses bearing_deg where positive means image-right.
/// Consumers can convert that convention with their own parameters.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectedTarget {

    // This member is not documented.
    #[allow(missing_docs)]
    pub object_kind: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fruit_kind: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_x1: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_y1: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_x2: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_y2: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bearing_deg: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub has_distance: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub distance_m: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pick_allowed: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub target_confirmed: bool,

}



impl Default for DetectedTarget {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !snu_robot_interfaces__msg__DetectedTarget__init(&mut msg as *mut _) {
        panic!("Call to snu_robot_interfaces__msg__DetectedTarget__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DetectedTarget {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__DetectedTarget__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__DetectedTarget__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__DetectedTarget__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DetectedTarget {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DetectedTarget where Self: Sized {
  const TYPE_NAME: &'static str = "snu_robot_interfaces/msg/DetectedTarget";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__DetectedTarget() }
  }
}


#[link(name = "snu_robot_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__DetectedTargetArray() -> *const std::ffi::c_void;
}

#[link(name = "snu_robot_interfaces__rosidl_generator_c")]
extern "C" {
    fn snu_robot_interfaces__msg__DetectedTargetArray__init(msg: *mut DetectedTargetArray) -> bool;
    fn snu_robot_interfaces__msg__DetectedTargetArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DetectedTargetArray>, size: usize) -> bool;
    fn snu_robot_interfaces__msg__DetectedTargetArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DetectedTargetArray>);
    fn snu_robot_interfaces__msg__DetectedTargetArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DetectedTargetArray>, out_seq: *mut rosidl_runtime_rs::Sequence<DetectedTargetArray>) -> bool;
}

// Corresponds to snu_robot_interfaces__msg__DetectedTargetArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectedTargetArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub targets: rosidl_runtime_rs::Sequence<super::super::msg::rmw::DetectedTarget>,

}



impl Default for DetectedTargetArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !snu_robot_interfaces__msg__DetectedTargetArray__init(&mut msg as *mut _) {
        panic!("Call to snu_robot_interfaces__msg__DetectedTargetArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DetectedTargetArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__DetectedTargetArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__DetectedTargetArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__DetectedTargetArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DetectedTargetArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DetectedTargetArray where Self: Sized {
  const TYPE_NAME: &'static str = "snu_robot_interfaces/msg/DetectedTargetArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__DetectedTargetArray() }
  }
}


#[link(name = "snu_robot_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__FourWheelCommand() -> *const std::ffi::c_void;
}

#[link(name = "snu_robot_interfaces__rosidl_generator_c")]
extern "C" {
    fn snu_robot_interfaces__msg__FourWheelCommand__init(msg: *mut FourWheelCommand) -> bool;
    fn snu_robot_interfaces__msg__FourWheelCommand__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FourWheelCommand>, size: usize) -> bool;
    fn snu_robot_interfaces__msg__FourWheelCommand__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FourWheelCommand>);
    fn snu_robot_interfaces__msg__FourWheelCommand__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FourWheelCommand>, out_seq: *mut rosidl_runtime_rs::Sequence<FourWheelCommand>) -> bool;
}

// Corresponds to snu_robot_interfaces__msg__FourWheelCommand
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Command for four independently driven wheels.
///
/// A low-level motor driver should convert this command to actual motor control.
/// Use VELOCITY_RAD_S when the motor driver has velocity control.
/// Use NORMALIZED_POWER when the motor driver accepts open-loop power/PWM.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FourWheelCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub command_mode: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub front_left: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub front_right: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rear_left: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rear_right: f32,

}

impl FourWheelCommand {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const VELOCITY_RAD_S: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const NORMALIZED_POWER: u8 = 2;

}


impl Default for FourWheelCommand {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !snu_robot_interfaces__msg__FourWheelCommand__init(&mut msg as *mut _) {
        panic!("Call to snu_robot_interfaces__msg__FourWheelCommand__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FourWheelCommand {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__FourWheelCommand__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__FourWheelCommand__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__FourWheelCommand__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FourWheelCommand {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FourWheelCommand where Self: Sized {
  const TYPE_NAME: &'static str = "snu_robot_interfaces/msg/FourWheelCommand";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__FourWheelCommand() }
  }
}


#[link(name = "snu_robot_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__GripperCommand() -> *const std::ffi::c_void;
}

#[link(name = "snu_robot_interfaces__rosidl_generator_c")]
extern "C" {
    fn snu_robot_interfaces__msg__GripperCommand__init(msg: *mut GripperCommand) -> bool;
    fn snu_robot_interfaces__msg__GripperCommand__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GripperCommand>, size: usize) -> bool;
    fn snu_robot_interfaces__msg__GripperCommand__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GripperCommand>);
    fn snu_robot_interfaces__msg__GripperCommand__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GripperCommand>, out_seq: *mut rosidl_runtime_rs::Sequence<GripperCommand>) -> bool;
}

// Corresponds to snu_robot_interfaces__msg__GripperCommand
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// Command for the front basket/gripper mechanism.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GripperCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub command: u8,

    /// Used by SET_OPENING. Ignored by simple OPEN/CLOSE grippers.
    pub opening_m: f32,

    /// Optional normalized effort or motor power, 0..1.
    pub effort: f32,

}

impl GripperCommand {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const OPEN: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const CLOSE: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const STOP: u8 = 3;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SET_OPENING: u8 = 4;

}


impl Default for GripperCommand {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !snu_robot_interfaces__msg__GripperCommand__init(&mut msg as *mut _) {
        panic!("Call to snu_robot_interfaces__msg__GripperCommand__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GripperCommand {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__GripperCommand__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__GripperCommand__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__GripperCommand__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GripperCommand {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GripperCommand where Self: Sized {
  const TYPE_NAME: &'static str = "snu_robot_interfaces/msg/GripperCommand";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__GripperCommand() }
  }
}


#[link(name = "snu_robot_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__GripperState() -> *const std::ffi::c_void;
}

#[link(name = "snu_robot_interfaces__rosidl_generator_c")]
extern "C" {
    fn snu_robot_interfaces__msg__GripperState__init(msg: *mut GripperState) -> bool;
    fn snu_robot_interfaces__msg__GripperState__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GripperState>, size: usize) -> bool;
    fn snu_robot_interfaces__msg__GripperState__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GripperState>);
    fn snu_robot_interfaces__msg__GripperState__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GripperState>, out_seq: *mut rosidl_runtime_rs::Sequence<GripperState>) -> bool;
}

// Corresponds to snu_robot_interfaces__msg__GripperState
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// State reported by the front basket/gripper mechanism.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GripperState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub is_open: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub is_closed: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub has_object: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub opening_m: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub effort: f32,

}



impl Default for GripperState {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !snu_robot_interfaces__msg__GripperState__init(&mut msg as *mut _) {
        panic!("Call to snu_robot_interfaces__msg__GripperState__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GripperState {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__GripperState__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__GripperState__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__GripperState__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GripperState {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GripperState where Self: Sized {
  const TYPE_NAME: &'static str = "snu_robot_interfaces/msg/GripperState";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__GripperState() }
  }
}


#[link(name = "snu_robot_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__PerceivedObject() -> *const std::ffi::c_void;
}

#[link(name = "snu_robot_interfaces__rosidl_generator_c")]
extern "C" {
    fn snu_robot_interfaces__msg__PerceivedObject__init(msg: *mut PerceivedObject) -> bool;
    fn snu_robot_interfaces__msg__PerceivedObject__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PerceivedObject>, size: usize) -> bool;
    fn snu_robot_interfaces__msg__PerceivedObject__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PerceivedObject>);
    fn snu_robot_interfaces__msg__PerceivedObject__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PerceivedObject>, out_seq: *mut rosidl_runtime_rs::Sequence<PerceivedObject>) -> bool;
}

// Corresponds to snu_robot_interfaces__msg__PerceivedObject
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]

/// One camera-visible object enriched with distance and navigation role.
///
/// The detector should publish every relevant object, not only the current target.
/// Mission logic or perception post-processing assigns navigation_role:
/// target objects become approach goals, non-target objects become obstacles.

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PerceivedObject {

    // This member is not documented.
    #[allow(missing_docs)]
    pub object_kind: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fruit_kind: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub navigation_role: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_x1: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_y1: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_x2: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_y2: f32,

    /// Current YOLO convention: positive means image-right.
    pub bearing_deg: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub has_distance: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub distance_m: f32,

    /// Optional physical radius used when expanding semantic obstacles.
    /// If this is 0, consumers use their configured default radius.
    pub obstacle_radius_m: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pick_allowed: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub target_confirmed: bool,

}

impl PerceivedObject {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const ROLE_UNKNOWN: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const ROLE_TARGET: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const ROLE_OBSTACLE: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const ROLE_IGNORE: u8 = 3;

}


impl Default for PerceivedObject {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !snu_robot_interfaces__msg__PerceivedObject__init(&mut msg as *mut _) {
        panic!("Call to snu_robot_interfaces__msg__PerceivedObject__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PerceivedObject {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__PerceivedObject__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__PerceivedObject__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__PerceivedObject__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PerceivedObject {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PerceivedObject where Self: Sized {
  const TYPE_NAME: &'static str = "snu_robot_interfaces/msg/PerceivedObject";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__PerceivedObject() }
  }
}


#[link(name = "snu_robot_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__PerceivedObjectArray() -> *const std::ffi::c_void;
}

#[link(name = "snu_robot_interfaces__rosidl_generator_c")]
extern "C" {
    fn snu_robot_interfaces__msg__PerceivedObjectArray__init(msg: *mut PerceivedObjectArray) -> bool;
    fn snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PerceivedObjectArray>, size: usize) -> bool;
    fn snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PerceivedObjectArray>);
    fn snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PerceivedObjectArray>, out_seq: *mut rosidl_runtime_rs::Sequence<PerceivedObjectArray>) -> bool;
}

// Corresponds to snu_robot_interfaces__msg__PerceivedObjectArray
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PerceivedObjectArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub objects: rosidl_runtime_rs::Sequence<super::super::msg::rmw::PerceivedObject>,

}



impl Default for PerceivedObjectArray {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !snu_robot_interfaces__msg__PerceivedObjectArray__init(&mut msg as *mut _) {
        panic!("Call to snu_robot_interfaces__msg__PerceivedObjectArray__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PerceivedObjectArray {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { snu_robot_interfaces__msg__PerceivedObjectArray__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PerceivedObjectArray {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PerceivedObjectArray where Self: Sized {
  const TYPE_NAME: &'static str = "snu_robot_interfaces/msg/PerceivedObjectArray";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__snu_robot_interfaces__msg__PerceivedObjectArray() }
  }
}


