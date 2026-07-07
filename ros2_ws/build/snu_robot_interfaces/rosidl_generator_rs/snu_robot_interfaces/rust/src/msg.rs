#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to snu_robot_interfaces__msg__DetectedTarget
/// One target produced by the camera detector and distance provider.
///
/// The current YOLO branch uses bearing_deg where positive means image-right.
/// Consumers can convert that convention with their own parameters.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectedTarget {

    // This member is not documented.
    #[allow(missing_docs)]
    pub object_kind: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fruit_kind: std::string::String,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::DetectedTarget::default())
  }
}

impl rosidl_runtime_rs::Message for DetectedTarget {
  type RmwMsg = super::msg::rmw::DetectedTarget;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        object_kind: msg.object_kind.as_str().into(),
        fruit_kind: msg.fruit_kind.as_str().into(),
        confidence: msg.confidence,
        bbox_x1: msg.bbox_x1,
        bbox_y1: msg.bbox_y1,
        bbox_x2: msg.bbox_x2,
        bbox_y2: msg.bbox_y2,
        bearing_deg: msg.bearing_deg,
        has_distance: msg.has_distance,
        distance_m: msg.distance_m,
        pick_allowed: msg.pick_allowed,
        target_confirmed: msg.target_confirmed,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        object_kind: msg.object_kind.as_str().into(),
        fruit_kind: msg.fruit_kind.as_str().into(),
      confidence: msg.confidence,
      bbox_x1: msg.bbox_x1,
      bbox_y1: msg.bbox_y1,
      bbox_x2: msg.bbox_x2,
      bbox_y2: msg.bbox_y2,
      bearing_deg: msg.bearing_deg,
      has_distance: msg.has_distance,
      distance_m: msg.distance_m,
      pick_allowed: msg.pick_allowed,
      target_confirmed: msg.target_confirmed,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      object_kind: msg.object_kind.to_string(),
      fruit_kind: msg.fruit_kind.to_string(),
      confidence: msg.confidence,
      bbox_x1: msg.bbox_x1,
      bbox_y1: msg.bbox_y1,
      bbox_x2: msg.bbox_x2,
      bbox_y2: msg.bbox_y2,
      bearing_deg: msg.bearing_deg,
      has_distance: msg.has_distance,
      distance_m: msg.distance_m,
      pick_allowed: msg.pick_allowed,
      target_confirmed: msg.target_confirmed,
    }
  }
}


// Corresponds to snu_robot_interfaces__msg__DetectedTargetArray

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DetectedTargetArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub targets: Vec<super::msg::DetectedTarget>,

}



impl Default for DetectedTargetArray {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::DetectedTargetArray::default())
  }
}

impl rosidl_runtime_rs::Message for DetectedTargetArray {
  type RmwMsg = super::msg::rmw::DetectedTargetArray;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        targets: msg.targets
          .into_iter()
          .map(|elem| super::msg::DetectedTarget::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        targets: msg.targets
          .iter()
          .map(|elem| super::msg::DetectedTarget::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      targets: msg.targets
          .into_iter()
          .map(super::msg::DetectedTarget::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to snu_robot_interfaces__msg__FourWheelCommand
/// Command for four independently driven wheels.
///
/// A low-level motor driver should convert this command to actual motor control.
/// Use VELOCITY_RAD_S when the motor driver has velocity control.
/// Use NORMALIZED_POWER when the motor driver accepts open-loop power/PWM.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FourWheelCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::FourWheelCommand::default())
  }
}

impl rosidl_runtime_rs::Message for FourWheelCommand {
  type RmwMsg = super::msg::rmw::FourWheelCommand;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        command_mode: msg.command_mode,
        front_left: msg.front_left,
        front_right: msg.front_right,
        rear_left: msg.rear_left,
        rear_right: msg.rear_right,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      command_mode: msg.command_mode,
      front_left: msg.front_left,
      front_right: msg.front_right,
      rear_left: msg.rear_left,
      rear_right: msg.rear_right,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      command_mode: msg.command_mode,
      front_left: msg.front_left,
      front_right: msg.front_right,
      rear_left: msg.rear_left,
      rear_right: msg.rear_right,
    }
  }
}


// Corresponds to snu_robot_interfaces__msg__GripperCommand
/// Command for the front basket/gripper mechanism.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GripperCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::GripperCommand::default())
  }
}

impl rosidl_runtime_rs::Message for GripperCommand {
  type RmwMsg = super::msg::rmw::GripperCommand;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        command: msg.command,
        opening_m: msg.opening_m,
        effort: msg.effort,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      command: msg.command,
      opening_m: msg.opening_m,
      effort: msg.effort,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      command: msg.command,
      opening_m: msg.opening_m,
      effort: msg.effort,
    }
  }
}


// Corresponds to snu_robot_interfaces__msg__GripperState
/// State reported by the front basket/gripper mechanism.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GripperState {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::GripperState::default())
  }
}

impl rosidl_runtime_rs::Message for GripperState {
  type RmwMsg = super::msg::rmw::GripperState;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        is_open: msg.is_open,
        is_closed: msg.is_closed,
        has_object: msg.has_object,
        opening_m: msg.opening_m,
        effort: msg.effort,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      is_open: msg.is_open,
      is_closed: msg.is_closed,
      has_object: msg.has_object,
      opening_m: msg.opening_m,
      effort: msg.effort,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      is_open: msg.is_open,
      is_closed: msg.is_closed,
      has_object: msg.has_object,
      opening_m: msg.opening_m,
      effort: msg.effort,
    }
  }
}


// Corresponds to snu_robot_interfaces__msg__PerceivedObject
/// One camera-visible object enriched with distance and navigation role.
///
/// The detector should publish every relevant object, not only the current target.
/// Mission logic or perception post-processing assigns navigation_role:
/// target objects become approach goals, non-target objects become obstacles.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PerceivedObject {

    // This member is not documented.
    #[allow(missing_docs)]
    pub object_kind: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fruit_kind: std::string::String,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::PerceivedObject::default())
  }
}

impl rosidl_runtime_rs::Message for PerceivedObject {
  type RmwMsg = super::msg::rmw::PerceivedObject;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        object_kind: msg.object_kind.as_str().into(),
        fruit_kind: msg.fruit_kind.as_str().into(),
        navigation_role: msg.navigation_role,
        confidence: msg.confidence,
        bbox_x1: msg.bbox_x1,
        bbox_y1: msg.bbox_y1,
        bbox_x2: msg.bbox_x2,
        bbox_y2: msg.bbox_y2,
        bearing_deg: msg.bearing_deg,
        has_distance: msg.has_distance,
        distance_m: msg.distance_m,
        obstacle_radius_m: msg.obstacle_radius_m,
        pick_allowed: msg.pick_allowed,
        target_confirmed: msg.target_confirmed,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        object_kind: msg.object_kind.as_str().into(),
        fruit_kind: msg.fruit_kind.as_str().into(),
      navigation_role: msg.navigation_role,
      confidence: msg.confidence,
      bbox_x1: msg.bbox_x1,
      bbox_y1: msg.bbox_y1,
      bbox_x2: msg.bbox_x2,
      bbox_y2: msg.bbox_y2,
      bearing_deg: msg.bearing_deg,
      has_distance: msg.has_distance,
      distance_m: msg.distance_m,
      obstacle_radius_m: msg.obstacle_radius_m,
      pick_allowed: msg.pick_allowed,
      target_confirmed: msg.target_confirmed,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      object_kind: msg.object_kind.to_string(),
      fruit_kind: msg.fruit_kind.to_string(),
      navigation_role: msg.navigation_role,
      confidence: msg.confidence,
      bbox_x1: msg.bbox_x1,
      bbox_y1: msg.bbox_y1,
      bbox_x2: msg.bbox_x2,
      bbox_y2: msg.bbox_y2,
      bearing_deg: msg.bearing_deg,
      has_distance: msg.has_distance,
      distance_m: msg.distance_m,
      obstacle_radius_m: msg.obstacle_radius_m,
      pick_allowed: msg.pick_allowed,
      target_confirmed: msg.target_confirmed,
    }
  }
}


// Corresponds to snu_robot_interfaces__msg__PerceivedObjectArray

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PerceivedObjectArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub objects: Vec<super::msg::PerceivedObject>,

}



impl Default for PerceivedObjectArray {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::PerceivedObjectArray::default())
  }
}

impl rosidl_runtime_rs::Message for PerceivedObjectArray {
  type RmwMsg = super::msg::rmw::PerceivedObjectArray;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        objects: msg.objects
          .into_iter()
          .map(|elem| super::msg::PerceivedObject::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        objects: msg.objects
          .iter()
          .map(|elem| super::msg::PerceivedObject::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      objects: msg.objects
          .into_iter()
          .map(super::msg::PerceivedObject::from_rmw_message)
          .collect(),
    }
  }
}


