#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "collision_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__collision_management__srv__GetCollisionStatus_Request() -> *const std::ffi::c_void;
}

#[link(name = "collision_management__rosidl_generator_c")]
extern "C" {
    fn collision_management__srv__GetCollisionStatus_Request__init(msg: *mut GetCollisionStatus_Request) -> bool;
    fn collision_management__srv__GetCollisionStatus_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetCollisionStatus_Request>, size: usize) -> bool;
    fn collision_management__srv__GetCollisionStatus_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetCollisionStatus_Request>);
    fn collision_management__srv__GetCollisionStatus_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetCollisionStatus_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<GetCollisionStatus_Request>) -> bool;
}

// Corresponds to collision_management__srv__GetCollisionStatus_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetCollisionStatus_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for GetCollisionStatus_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !collision_management__srv__GetCollisionStatus_Request__init(&mut msg as *mut _) {
        panic!("Call to collision_management__srv__GetCollisionStatus_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetCollisionStatus_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { collision_management__srv__GetCollisionStatus_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { collision_management__srv__GetCollisionStatus_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { collision_management__srv__GetCollisionStatus_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetCollisionStatus_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetCollisionStatus_Request where Self: Sized {
  const TYPE_NAME: &'static str = "collision_management/srv/GetCollisionStatus_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__collision_management__srv__GetCollisionStatus_Request() }
  }
}


#[link(name = "collision_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__collision_management__srv__GetCollisionStatus_Response() -> *const std::ffi::c_void;
}

#[link(name = "collision_management__rosidl_generator_c")]
extern "C" {
    fn collision_management__srv__GetCollisionStatus_Response__init(msg: *mut GetCollisionStatus_Response) -> bool;
    fn collision_management__srv__GetCollisionStatus_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetCollisionStatus_Response>, size: usize) -> bool;
    fn collision_management__srv__GetCollisionStatus_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetCollisionStatus_Response>);
    fn collision_management__srv__GetCollisionStatus_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetCollisionStatus_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<GetCollisionStatus_Response>) -> bool;
}

// Corresponds to collision_management__srv__GetCollisionStatus_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetCollisionStatus_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub in_collision: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub status: sensor_msgs::msg::rmw::JointState,

}



impl Default for GetCollisionStatus_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !collision_management__srv__GetCollisionStatus_Response__init(&mut msg as *mut _) {
        panic!("Call to collision_management__srv__GetCollisionStatus_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetCollisionStatus_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { collision_management__srv__GetCollisionStatus_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { collision_management__srv__GetCollisionStatus_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { collision_management__srv__GetCollisionStatus_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetCollisionStatus_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetCollisionStatus_Response where Self: Sized {
  const TYPE_NAME: &'static str = "collision_management/srv/GetCollisionStatus_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__collision_management__srv__GetCollisionStatus_Response() }
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


