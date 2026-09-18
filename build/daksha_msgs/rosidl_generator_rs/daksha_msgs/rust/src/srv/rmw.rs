#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "daksha_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__daksha_msgs__srv__StartRecord_Request() -> *const std::ffi::c_void;
}

#[link(name = "daksha_msgs__rosidl_generator_c")]
extern "C" {
    fn daksha_msgs__srv__StartRecord_Request__init(msg: *mut StartRecord_Request) -> bool;
    fn daksha_msgs__srv__StartRecord_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<StartRecord_Request>, size: usize) -> bool;
    fn daksha_msgs__srv__StartRecord_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<StartRecord_Request>);
    fn daksha_msgs__srv__StartRecord_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<StartRecord_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<StartRecord_Request>) -> bool;
}

// Corresponds to daksha_msgs__srv__StartRecord_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartRecord_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub dataset_name: rosidl_runtime_rs::String,


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
    unsafe {
      let mut msg = std::mem::zeroed();
      if !daksha_msgs__srv__StartRecord_Request__init(&mut msg as *mut _) {
        panic!("Call to daksha_msgs__srv__StartRecord_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for StartRecord_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartRecord_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartRecord_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartRecord_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for StartRecord_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for StartRecord_Request where Self: Sized {
  const TYPE_NAME: &'static str = "daksha_msgs/srv/StartRecord_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__daksha_msgs__srv__StartRecord_Request() }
  }
}


#[link(name = "daksha_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__daksha_msgs__srv__StartRecord_Response() -> *const std::ffi::c_void;
}

#[link(name = "daksha_msgs__rosidl_generator_c")]
extern "C" {
    fn daksha_msgs__srv__StartRecord_Response__init(msg: *mut StartRecord_Response) -> bool;
    fn daksha_msgs__srv__StartRecord_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<StartRecord_Response>, size: usize) -> bool;
    fn daksha_msgs__srv__StartRecord_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<StartRecord_Response>);
    fn daksha_msgs__srv__StartRecord_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<StartRecord_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<StartRecord_Response>) -> bool;
}

// Corresponds to daksha_msgs__srv__StartRecord_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartRecord_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for StartRecord_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !daksha_msgs__srv__StartRecord_Response__init(&mut msg as *mut _) {
        panic!("Call to daksha_msgs__srv__StartRecord_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for StartRecord_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartRecord_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartRecord_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartRecord_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for StartRecord_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for StartRecord_Response where Self: Sized {
  const TYPE_NAME: &'static str = "daksha_msgs/srv/StartRecord_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__daksha_msgs__srv__StartRecord_Response() }
  }
}


#[link(name = "daksha_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__daksha_msgs__srv__StartReplay_Request() -> *const std::ffi::c_void;
}

#[link(name = "daksha_msgs__rosidl_generator_c")]
extern "C" {
    fn daksha_msgs__srv__StartReplay_Request__init(msg: *mut StartReplay_Request) -> bool;
    fn daksha_msgs__srv__StartReplay_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<StartReplay_Request>, size: usize) -> bool;
    fn daksha_msgs__srv__StartReplay_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<StartReplay_Request>);
    fn daksha_msgs__srv__StartReplay_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<StartReplay_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<StartReplay_Request>) -> bool;
}

// Corresponds to daksha_msgs__srv__StartReplay_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartReplay_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub dataset_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub episode_index: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub speed: f32,

}



impl Default for StartReplay_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !daksha_msgs__srv__StartReplay_Request__init(&mut msg as *mut _) {
        panic!("Call to daksha_msgs__srv__StartReplay_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for StartReplay_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartReplay_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartReplay_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartReplay_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for StartReplay_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for StartReplay_Request where Self: Sized {
  const TYPE_NAME: &'static str = "daksha_msgs/srv/StartReplay_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__daksha_msgs__srv__StartReplay_Request() }
  }
}


#[link(name = "daksha_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__daksha_msgs__srv__StartReplay_Response() -> *const std::ffi::c_void;
}

#[link(name = "daksha_msgs__rosidl_generator_c")]
extern "C" {
    fn daksha_msgs__srv__StartReplay_Response__init(msg: *mut StartReplay_Response) -> bool;
    fn daksha_msgs__srv__StartReplay_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<StartReplay_Response>, size: usize) -> bool;
    fn daksha_msgs__srv__StartReplay_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<StartReplay_Response>);
    fn daksha_msgs__srv__StartReplay_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<StartReplay_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<StartReplay_Response>) -> bool;
}

// Corresponds to daksha_msgs__srv__StartReplay_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartReplay_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for StartReplay_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !daksha_msgs__srv__StartReplay_Response__init(&mut msg as *mut _) {
        panic!("Call to daksha_msgs__srv__StartReplay_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for StartReplay_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartReplay_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartReplay_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { daksha_msgs__srv__StartReplay_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for StartReplay_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for StartReplay_Response where Self: Sized {
  const TYPE_NAME: &'static str = "daksha_msgs/srv/StartReplay_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__daksha_msgs__srv__StartReplay_Response() }
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


