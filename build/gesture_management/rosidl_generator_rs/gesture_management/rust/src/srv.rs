#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to gesture_management__srv__StartRecording_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartRecording_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub topic_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub action: std::string::String,

}



impl Default for StartRecording_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::StartRecording_Request::default())
  }
}

impl rosidl_runtime_rs::Message for StartRecording_Request {
  type RmwMsg = super::srv::rmw::StartRecording_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        topic_name: msg.topic_name.as_str().into(),
        recording_name: msg.recording_name.as_str().into(),
        action: msg.action.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        topic_name: msg.topic_name.as_str().into(),
        recording_name: msg.recording_name.as_str().into(),
        action: msg.action.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      topic_name: msg.topic_name.to_string(),
      recording_name: msg.recording_name.to_string(),
      action: msg.action.to_string(),
    }
  }
}


// Corresponds to gesture_management__srv__StartRecording_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartRecording_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for StartRecording_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::StartRecording_Response::default())
  }
}

impl rosidl_runtime_rs::Message for StartRecording_Response {
  type RmwMsg = super::srv::rmw::StartRecording_Response;

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


// Corresponds to gesture_management__srv__ReplayRecording_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ReplayRecording_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub output_topic: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub replay_speed: f32,

}



impl Default for ReplayRecording_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ReplayRecording_Request::default())
  }
}

impl rosidl_runtime_rs::Message for ReplayRecording_Request {
  type RmwMsg = super::srv::rmw::ReplayRecording_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        recording_name: msg.recording_name.as_str().into(),
        output_topic: msg.output_topic.as_str().into(),
        replay_speed: msg.replay_speed,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        recording_name: msg.recording_name.as_str().into(),
        output_topic: msg.output_topic.as_str().into(),
      replay_speed: msg.replay_speed,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      recording_name: msg.recording_name.to_string(),
      output_topic: msg.output_topic.to_string(),
      replay_speed: msg.replay_speed,
    }
  }
}


// Corresponds to gesture_management__srv__ReplayRecording_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ReplayRecording_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for ReplayRecording_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ReplayRecording_Response::default())
  }
}

impl rosidl_runtime_rs::Message for ReplayRecording_Response {
  type RmwMsg = super::srv::rmw::ReplayRecording_Response;

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


// Corresponds to gesture_management__srv__PlayRecording_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlayRecording_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub output_topic: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub replay_speed: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat_mode: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat_count: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub interval_s: f32,

}



impl Default for PlayRecording_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::PlayRecording_Request::default())
  }
}

impl rosidl_runtime_rs::Message for PlayRecording_Request {
  type RmwMsg = super::srv::rmw::PlayRecording_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        recording_name: msg.recording_name.as_str().into(),
        output_topic: msg.output_topic.as_str().into(),
        replay_speed: msg.replay_speed,
        repeat_mode: msg.repeat_mode.as_str().into(),
        repeat_count: msg.repeat_count,
        interval_s: msg.interval_s,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        recording_name: msg.recording_name.as_str().into(),
        output_topic: msg.output_topic.as_str().into(),
      replay_speed: msg.replay_speed,
        repeat_mode: msg.repeat_mode.as_str().into(),
      repeat_count: msg.repeat_count,
      interval_s: msg.interval_s,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      recording_name: msg.recording_name.to_string(),
      output_topic: msg.output_topic.to_string(),
      replay_speed: msg.replay_speed,
      repeat_mode: msg.repeat_mode.to_string(),
      repeat_count: msg.repeat_count,
      interval_s: msg.interval_s,
    }
  }
}


// Corresponds to gesture_management__srv__PlayRecording_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlayRecording_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for PlayRecording_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::PlayRecording_Response::default())
  }
}

impl rosidl_runtime_rs::Message for PlayRecording_Response {
  type RmwMsg = super::srv::rmw::PlayRecording_Response;

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


// Corresponds to gesture_management__srv__PlaySequence_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlaySequence_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub sequence_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_names: Vec<std::string::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub output_topic: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub replay_speed: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat_mode: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat_count: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub interval_s: f32,

}



impl Default for PlaySequence_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::PlaySequence_Request::default())
  }
}

impl rosidl_runtime_rs::Message for PlaySequence_Request {
  type RmwMsg = super::srv::rmw::PlaySequence_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        sequence_name: msg.sequence_name.as_str().into(),
        recording_names: msg.recording_names
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        output_topic: msg.output_topic.as_str().into(),
        replay_speed: msg.replay_speed,
        repeat_mode: msg.repeat_mode.as_str().into(),
        repeat_count: msg.repeat_count,
        interval_s: msg.interval_s,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        sequence_name: msg.sequence_name.as_str().into(),
        recording_names: msg.recording_names
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        output_topic: msg.output_topic.as_str().into(),
      replay_speed: msg.replay_speed,
        repeat_mode: msg.repeat_mode.as_str().into(),
      repeat_count: msg.repeat_count,
      interval_s: msg.interval_s,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      sequence_name: msg.sequence_name.to_string(),
      recording_names: msg.recording_names
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
      output_topic: msg.output_topic.to_string(),
      replay_speed: msg.replay_speed,
      repeat_mode: msg.repeat_mode.to_string(),
      repeat_count: msg.repeat_count,
      interval_s: msg.interval_s,
    }
  }
}


// Corresponds to gesture_management__srv__PlaySequence_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlaySequence_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for PlaySequence_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::PlaySequence_Response::default())
  }
}

impl rosidl_runtime_rs::Message for PlaySequence_Response {
  type RmwMsg = super::srv::rmw::PlaySequence_Response;

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


// Corresponds to gesture_management__srv__SaveSequence_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SaveSequence_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_names: Vec<std::string::String>,

}



impl Default for SaveSequence_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::SaveSequence_Request::default())
  }
}

impl rosidl_runtime_rs::Message for SaveSequence_Request {
  type RmwMsg = super::srv::rmw::SaveSequence_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        name: msg.name.as_str().into(),
        recording_names: msg.recording_names
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        name: msg.name.as_str().into(),
        recording_names: msg.recording_names
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      name: msg.name.to_string(),
      recording_names: msg.recording_names
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
    }
  }
}


// Corresponds to gesture_management__srv__SaveSequence_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SaveSequence_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for SaveSequence_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::SaveSequence_Response::default())
  }
}

impl rosidl_runtime_rs::Message for SaveSequence_Response {
  type RmwMsg = super::srv::rmw::SaveSequence_Response;

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


// Corresponds to gesture_management__srv__DeleteSequence_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DeleteSequence_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub name: std::string::String,

}



impl Default for DeleteSequence_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::DeleteSequence_Request::default())
  }
}

impl rosidl_runtime_rs::Message for DeleteSequence_Request {
  type RmwMsg = super::srv::rmw::DeleteSequence_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        name: msg.name.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        name: msg.name.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      name: msg.name.to_string(),
    }
  }
}


// Corresponds to gesture_management__srv__DeleteSequence_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DeleteSequence_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for DeleteSequence_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::DeleteSequence_Response::default())
  }
}

impl rosidl_runtime_rs::Message for DeleteSequence_Response {
  type RmwMsg = super::srv::rmw::DeleteSequence_Response;

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


// Corresponds to gesture_management__srv__ListSequences_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ListSequences_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for ListSequences_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ListSequences_Request::default())
  }
}

impl rosidl_runtime_rs::Message for ListSequences_Request {
  type RmwMsg = super::srv::rmw::ListSequences_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
    }
  }
}


// Corresponds to gesture_management__srv__ListSequences_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ListSequences_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub sequences_json: std::string::String,

}



impl Default for ListSequences_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ListSequences_Response::default())
  }
}

impl rosidl_runtime_rs::Message for ListSequences_Response {
  type RmwMsg = super::srv::rmw::ListSequences_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        sequences_json: msg.sequences_json.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        sequences_json: msg.sequences_json.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      sequences_json: msg.sequences_json.to_string(),
    }
  }
}


// Corresponds to gesture_management__srv__GetReplayStatus_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetReplayStatus_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for GetReplayStatus_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetReplayStatus_Request::default())
  }
}

impl rosidl_runtime_rs::Message for GetReplayStatus_Request {
  type RmwMsg = super::srv::rmw::GetReplayStatus_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
    }
  }
}


// Corresponds to gesture_management__srv__GetReplayStatus_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetReplayStatus_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub status_json: std::string::String,

}



impl Default for GetReplayStatus_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetReplayStatus_Response::default())
  }
}

impl rosidl_runtime_rs::Message for GetReplayStatus_Response {
  type RmwMsg = super::srv::rmw::GetReplayStatus_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        status_json: msg.status_json.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        status_json: msg.status_json.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      status_json: msg.status_json.to_string(),
    }
  }
}






#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__StartRecording() -> *const std::ffi::c_void;
}

// Corresponds to gesture_management__srv__StartRecording
#[allow(missing_docs, non_camel_case_types)]
pub struct StartRecording;

impl rosidl_runtime_rs::Service for StartRecording {
    type Request = StartRecording_Request;
    type Response = StartRecording_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__StartRecording() }
    }
}




#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__ReplayRecording() -> *const std::ffi::c_void;
}

// Corresponds to gesture_management__srv__ReplayRecording
#[allow(missing_docs, non_camel_case_types)]
pub struct ReplayRecording;

impl rosidl_runtime_rs::Service for ReplayRecording {
    type Request = ReplayRecording_Request;
    type Response = ReplayRecording_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__ReplayRecording() }
    }
}




#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__PlayRecording() -> *const std::ffi::c_void;
}

// Corresponds to gesture_management__srv__PlayRecording
#[allow(missing_docs, non_camel_case_types)]
pub struct PlayRecording;

impl rosidl_runtime_rs::Service for PlayRecording {
    type Request = PlayRecording_Request;
    type Response = PlayRecording_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__PlayRecording() }
    }
}




#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__PlaySequence() -> *const std::ffi::c_void;
}

// Corresponds to gesture_management__srv__PlaySequence
#[allow(missing_docs, non_camel_case_types)]
pub struct PlaySequence;

impl rosidl_runtime_rs::Service for PlaySequence {
    type Request = PlaySequence_Request;
    type Response = PlaySequence_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__PlaySequence() }
    }
}




#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__SaveSequence() -> *const std::ffi::c_void;
}

// Corresponds to gesture_management__srv__SaveSequence
#[allow(missing_docs, non_camel_case_types)]
pub struct SaveSequence;

impl rosidl_runtime_rs::Service for SaveSequence {
    type Request = SaveSequence_Request;
    type Response = SaveSequence_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__SaveSequence() }
    }
}




#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__DeleteSequence() -> *const std::ffi::c_void;
}

// Corresponds to gesture_management__srv__DeleteSequence
#[allow(missing_docs, non_camel_case_types)]
pub struct DeleteSequence;

impl rosidl_runtime_rs::Service for DeleteSequence {
    type Request = DeleteSequence_Request;
    type Response = DeleteSequence_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__DeleteSequence() }
    }
}




#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__ListSequences() -> *const std::ffi::c_void;
}

// Corresponds to gesture_management__srv__ListSequences
#[allow(missing_docs, non_camel_case_types)]
pub struct ListSequences;

impl rosidl_runtime_rs::Service for ListSequences {
    type Request = ListSequences_Request;
    type Response = ListSequences_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__ListSequences() }
    }
}




#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__GetReplayStatus() -> *const std::ffi::c_void;
}

// Corresponds to gesture_management__srv__GetReplayStatus
#[allow(missing_docs, non_camel_case_types)]
pub struct GetReplayStatus;

impl rosidl_runtime_rs::Service for GetReplayStatus {
    type Request = GetReplayStatus_Request;
    type Response = GetReplayStatus_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__gesture_management__srv__GetReplayStatus() }
    }
}


