#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to robot_object_detector_ros__msg__Detection2D

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection2D {

    // This member is not documented.
    #[allow(missing_docs)]
    pub class_id: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub class_name: std::string::String,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Detection2D::default())
  }
}

impl rosidl_runtime_rs::Message for Detection2D {
  type RmwMsg = super::msg::rmw::Detection2D;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        class_id: msg.class_id,
        class_name: msg.class_name.as_str().into(),
        confidence: msg.confidence,
        x1: msg.x1,
        y1: msg.y1,
        x2: msg.x2,
        y2: msg.y2,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      class_id: msg.class_id,
        class_name: msg.class_name.as_str().into(),
      confidence: msg.confidence,
      x1: msg.x1,
      y1: msg.y1,
      x2: msg.x2,
      y2: msg.y2,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      class_id: msg.class_id,
      class_name: msg.class_name.to_string(),
      confidence: msg.confidence,
      x1: msg.x1,
      y1: msg.y1,
      x2: msg.x2,
      y2: msg.y2,
    }
  }
}


// Corresponds to robot_object_detector_ros__msg__Detection2DArray

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Detection2DArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub detections: Vec<super::msg::Detection2D>,

}



impl Default for Detection2DArray {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Detection2DArray::default())
  }
}

impl rosidl_runtime_rs::Message for Detection2DArray {
  type RmwMsg = super::msg::rmw::Detection2DArray;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        detections: msg.detections
          .into_iter()
          .map(|elem| super::msg::Detection2D::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        detections: msg.detections
          .iter()
          .map(|elem| super::msg::Detection2D::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      detections: msg.detections
          .into_iter()
          .map(super::msg::Detection2D::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to robot_object_detector_ros__msg__FruitClassification

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FruitClassification {

    // This member is not documented.
    #[allow(missing_docs)]
    pub cube: super::msg::Detection2D,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fruit_kind: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pick_allowed: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub class_names: Vec<std::string::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub probabilities: Vec<f32>,

}



impl Default for FruitClassification {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::FruitClassification::default())
  }
}

impl rosidl_runtime_rs::Message for FruitClassification {
  type RmwMsg = super::msg::rmw::FruitClassification;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        cube: super::msg::Detection2D::into_rmw_message(std::borrow::Cow::Owned(msg.cube)).into_owned(),
        fruit_kind: msg.fruit_kind.as_str().into(),
        confidence: msg.confidence,
        pick_allowed: msg.pick_allowed,
        class_names: msg.class_names
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        probabilities: msg.probabilities.into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        cube: super::msg::Detection2D::into_rmw_message(std::borrow::Cow::Borrowed(&msg.cube)).into_owned(),
        fruit_kind: msg.fruit_kind.as_str().into(),
      confidence: msg.confidence,
      pick_allowed: msg.pick_allowed,
        class_names: msg.class_names
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        probabilities: msg.probabilities.as_slice().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      cube: super::msg::Detection2D::from_rmw_message(msg.cube),
      fruit_kind: msg.fruit_kind.to_string(),
      confidence: msg.confidence,
      pick_allowed: msg.pick_allowed,
      class_names: msg.class_names
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
      probabilities: msg.probabilities
          .into_iter()
          .collect(),
    }
  }
}


// Corresponds to robot_object_detector_ros__msg__FruitClassificationArray

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FruitClassificationArray {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub classifications: Vec<super::msg::FruitClassification>,

}



impl Default for FruitClassificationArray {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::FruitClassificationArray::default())
  }
}

impl rosidl_runtime_rs::Message for FruitClassificationArray {
  type RmwMsg = super::msg::rmw::FruitClassificationArray;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        classifications: msg.classifications
          .into_iter()
          .map(|elem| super::msg::FruitClassification::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
        classifications: msg.classifications
          .iter()
          .map(|elem| super::msg::FruitClassification::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      classifications: msg.classifications
          .into_iter()
          .map(super::msg::FruitClassification::from_rmw_message)
          .collect(),
    }
  }
}


