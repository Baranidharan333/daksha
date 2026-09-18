#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to daksha_msgs__srv__StartRecord_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartRecord_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub dataset_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub episode_length: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub record_hz: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub max_episodes: i32,

}



impl Default for StartRecord_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::StartRecord_Request::default())
  }
}

impl rosidl_runtime_rs::Message for StartRecord_Request {
  type RmwMsg = super::srv::rmw::StartRecord_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        dataset_name: msg.dataset_name.as_str().into(),
        episode_length: msg.episode_length,
        record_hz: msg.record_hz,
        max_episodes: msg.max_episodes,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        dataset_name: msg.dataset_name.as_str().into(),
      episode_length: msg.episode_length,
      record_hz: msg.record_hz,
      max_episodes: msg.max_episodes,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      dataset_name: msg.dataset_name.to_string(),
      episode_length: msg.episode_length,
      record_hz: msg.record_hz,
      max_episodes: msg.max_episodes,
    }
  }
}


// Corresponds to daksha_msgs__srv__StartRecord_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartRecord_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for StartRecord_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::StartRecord_Response::default())
  }
}

impl rosidl_runtime_rs::Message for StartRecord_Response {
  type RmwMsg = super::srv::rmw::StartRecord_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      message: msg.message.to_string(),
    }
  }
}


// Corresponds to daksha_msgs__srv__StartReplay_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartReplay_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub dataset_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub episode_index: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub speed: f32,

}



impl Default for StartReplay_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::StartReplay_Request::default())
  }
}

impl rosidl_runtime_rs::Message for StartReplay_Request {
  type RmwMsg = super::srv::rmw::StartReplay_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        dataset_name: msg.dataset_name.as_str().into(),
        episode_index: msg.episode_index,
        speed: msg.speed,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        dataset_name: msg.dataset_name.as_str().into(),
      episode_index: msg.episode_index,
      speed: msg.speed,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      dataset_name: msg.dataset_name.to_string(),
      episode_index: msg.episode_index,
      speed: msg.speed,
    }
  }
}


// Corresponds to daksha_msgs__srv__StartReplay_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartReplay_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for StartReplay_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::StartReplay_Response::default())
  }
}

impl rosidl_runtime_rs::Message for StartReplay_Response {
  type RmwMsg = super::srv::rmw::StartReplay_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      message: msg.message.to_string(),
    }
  }
}






#[link(name = "daksha_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__daksha_msgs__srv__StartRecord() -> *const std::ffi::c_void;
}

// Corresponds to daksha_msgs__srv__StartRecord
#[allow(missing_docs, non_camel_case_types)]
pub struct StartRecord;

impl rosidl_runtime_rs::Service for StartRecord {
    type Request = StartRecord_Request;
    type Response = StartRecord_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__daksha_msgs__srv__StartRecord() }
    }
}




#[link(name = "daksha_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__daksha_msgs__srv__StartReplay() -> *const std::ffi::c_void;
}

// Corresponds to daksha_msgs__srv__StartReplay
#[allow(missing_docs, non_camel_case_types)]
pub struct StartReplay;

impl rosidl_runtime_rs::Service for StartReplay {
    type Request = StartReplay_Request;
    type Response = StartReplay_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__daksha_msgs__srv__StartReplay() }
    }
}


