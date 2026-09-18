#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to collision_management__srv__GetCollisionStatus_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetCollisionStatus_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for GetCollisionStatus_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetCollisionStatus_Request::default())
  }
}

impl rosidl_runtime_rs::Message for GetCollisionStatus_Request {
  type RmwMsg = super::srv::rmw::GetCollisionStatus_Request;

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


// Corresponds to collision_management__srv__GetCollisionStatus_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetCollisionStatus_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub in_collision: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub status: sensor_msgs::msg::JointState,

}



impl Default for GetCollisionStatus_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetCollisionStatus_Response::default())
  }
}

impl rosidl_runtime_rs::Message for GetCollisionStatus_Response {
  type RmwMsg = super::srv::rmw::GetCollisionStatus_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        in_collision: msg.in_collision,
        status: sensor_msgs::msg::JointState::into_rmw_message(std::borrow::Cow::Owned(msg.status)).into_owned(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      in_collision: msg.in_collision,
        status: sensor_msgs::msg::JointState::into_rmw_message(std::borrow::Cow::Borrowed(&msg.status)).into_owned(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      in_collision: msg.in_collision,
      status: sensor_msgs::msg::JointState::from_rmw_message(msg.status),
    }
  }
}






#[link(name = "collision_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__collision_management__srv__GetCollisionStatus() -> *const std::ffi::c_void;
}

// Corresponds to collision_management__srv__GetCollisionStatus
#[allow(missing_docs, non_camel_case_types)]
pub struct GetCollisionStatus;

impl rosidl_runtime_rs::Service for GetCollisionStatus {
    type Request = GetCollisionStatus_Request;
    type Response = GetCollisionStatus_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__collision_management__srv__GetCollisionStatus() }
    }
}


