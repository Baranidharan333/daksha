#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__StartRecording_Request() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__StartRecording_Request__init(msg: *mut StartRecording_Request) -> bool;
    fn gesture_management__srv__StartRecording_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<StartRecording_Request>, size: usize) -> bool;
    fn gesture_management__srv__StartRecording_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<StartRecording_Request>);
    fn gesture_management__srv__StartRecording_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<StartRecording_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<StartRecording_Request>) -> bool;
}

// Corresponds to gesture_management__srv__StartRecording_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartRecording_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub topic_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub action: rosidl_runtime_rs::String,

}



impl Default for StartRecording_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__StartRecording_Request__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__StartRecording_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for StartRecording_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__StartRecording_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__StartRecording_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__StartRecording_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for StartRecording_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for StartRecording_Request where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/StartRecording_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__StartRecording_Request() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__StartRecording_Response() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__StartRecording_Response__init(msg: *mut StartRecording_Response) -> bool;
    fn gesture_management__srv__StartRecording_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<StartRecording_Response>, size: usize) -> bool;
    fn gesture_management__srv__StartRecording_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<StartRecording_Response>);
    fn gesture_management__srv__StartRecording_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<StartRecording_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<StartRecording_Response>) -> bool;
}

// Corresponds to gesture_management__srv__StartRecording_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct StartRecording_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for StartRecording_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__StartRecording_Response__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__StartRecording_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for StartRecording_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__StartRecording_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__StartRecording_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__StartRecording_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for StartRecording_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for StartRecording_Response where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/StartRecording_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__StartRecording_Response() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__ReplayRecording_Request() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__ReplayRecording_Request__init(msg: *mut ReplayRecording_Request) -> bool;
    fn gesture_management__srv__ReplayRecording_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ReplayRecording_Request>, size: usize) -> bool;
    fn gesture_management__srv__ReplayRecording_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ReplayRecording_Request>);
    fn gesture_management__srv__ReplayRecording_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ReplayRecording_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<ReplayRecording_Request>) -> bool;
}

// Corresponds to gesture_management__srv__ReplayRecording_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ReplayRecording_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub output_topic: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub replay_speed: f32,

}



impl Default for ReplayRecording_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__ReplayRecording_Request__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__ReplayRecording_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ReplayRecording_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ReplayRecording_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ReplayRecording_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ReplayRecording_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ReplayRecording_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ReplayRecording_Request where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/ReplayRecording_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__ReplayRecording_Request() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__ReplayRecording_Response() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__ReplayRecording_Response__init(msg: *mut ReplayRecording_Response) -> bool;
    fn gesture_management__srv__ReplayRecording_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ReplayRecording_Response>, size: usize) -> bool;
    fn gesture_management__srv__ReplayRecording_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ReplayRecording_Response>);
    fn gesture_management__srv__ReplayRecording_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ReplayRecording_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<ReplayRecording_Response>) -> bool;
}

// Corresponds to gesture_management__srv__ReplayRecording_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ReplayRecording_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for ReplayRecording_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__ReplayRecording_Response__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__ReplayRecording_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ReplayRecording_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ReplayRecording_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ReplayRecording_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ReplayRecording_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ReplayRecording_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ReplayRecording_Response where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/ReplayRecording_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__ReplayRecording_Response() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__PlayRecording_Request() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__PlayRecording_Request__init(msg: *mut PlayRecording_Request) -> bool;
    fn gesture_management__srv__PlayRecording_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PlayRecording_Request>, size: usize) -> bool;
    fn gesture_management__srv__PlayRecording_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PlayRecording_Request>);
    fn gesture_management__srv__PlayRecording_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PlayRecording_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<PlayRecording_Request>) -> bool;
}

// Corresponds to gesture_management__srv__PlayRecording_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlayRecording_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub output_topic: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub replay_speed: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat_mode: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat_count: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub interval_s: f32,

}



impl Default for PlayRecording_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__PlayRecording_Request__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__PlayRecording_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PlayRecording_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlayRecording_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlayRecording_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlayRecording_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PlayRecording_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PlayRecording_Request where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/PlayRecording_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__PlayRecording_Request() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__PlayRecording_Response() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__PlayRecording_Response__init(msg: *mut PlayRecording_Response) -> bool;
    fn gesture_management__srv__PlayRecording_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PlayRecording_Response>, size: usize) -> bool;
    fn gesture_management__srv__PlayRecording_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PlayRecording_Response>);
    fn gesture_management__srv__PlayRecording_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PlayRecording_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<PlayRecording_Response>) -> bool;
}

// Corresponds to gesture_management__srv__PlayRecording_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlayRecording_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for PlayRecording_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__PlayRecording_Response__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__PlayRecording_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PlayRecording_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlayRecording_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlayRecording_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlayRecording_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PlayRecording_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PlayRecording_Response where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/PlayRecording_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__PlayRecording_Response() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__PlaySequence_Request() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__PlaySequence_Request__init(msg: *mut PlaySequence_Request) -> bool;
    fn gesture_management__srv__PlaySequence_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PlaySequence_Request>, size: usize) -> bool;
    fn gesture_management__srv__PlaySequence_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PlaySequence_Request>);
    fn gesture_management__srv__PlaySequence_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PlaySequence_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<PlaySequence_Request>) -> bool;
}

// Corresponds to gesture_management__srv__PlaySequence_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlaySequence_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub sequence_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_names: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub output_topic: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub replay_speed: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat_mode: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub repeat_count: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub interval_s: f32,

}



impl Default for PlaySequence_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__PlaySequence_Request__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__PlaySequence_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PlaySequence_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlaySequence_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlaySequence_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlaySequence_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PlaySequence_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PlaySequence_Request where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/PlaySequence_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__PlaySequence_Request() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__PlaySequence_Response() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__PlaySequence_Response__init(msg: *mut PlaySequence_Response) -> bool;
    fn gesture_management__srv__PlaySequence_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<PlaySequence_Response>, size: usize) -> bool;
    fn gesture_management__srv__PlaySequence_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<PlaySequence_Response>);
    fn gesture_management__srv__PlaySequence_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<PlaySequence_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<PlaySequence_Response>) -> bool;
}

// Corresponds to gesture_management__srv__PlaySequence_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct PlaySequence_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for PlaySequence_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__PlaySequence_Response__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__PlaySequence_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for PlaySequence_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlaySequence_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlaySequence_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__PlaySequence_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for PlaySequence_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for PlaySequence_Response where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/PlaySequence_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__PlaySequence_Response() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__SaveSequence_Request() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__SaveSequence_Request__init(msg: *mut SaveSequence_Request) -> bool;
    fn gesture_management__srv__SaveSequence_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<SaveSequence_Request>, size: usize) -> bool;
    fn gesture_management__srv__SaveSequence_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<SaveSequence_Request>);
    fn gesture_management__srv__SaveSequence_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<SaveSequence_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<SaveSequence_Request>) -> bool;
}

// Corresponds to gesture_management__srv__SaveSequence_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SaveSequence_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub recording_names: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,

}



impl Default for SaveSequence_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__SaveSequence_Request__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__SaveSequence_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for SaveSequence_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__SaveSequence_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__SaveSequence_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__SaveSequence_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for SaveSequence_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for SaveSequence_Request where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/SaveSequence_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__SaveSequence_Request() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__SaveSequence_Response() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__SaveSequence_Response__init(msg: *mut SaveSequence_Response) -> bool;
    fn gesture_management__srv__SaveSequence_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<SaveSequence_Response>, size: usize) -> bool;
    fn gesture_management__srv__SaveSequence_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<SaveSequence_Response>);
    fn gesture_management__srv__SaveSequence_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<SaveSequence_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<SaveSequence_Response>) -> bool;
}

// Corresponds to gesture_management__srv__SaveSequence_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct SaveSequence_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for SaveSequence_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__SaveSequence_Response__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__SaveSequence_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for SaveSequence_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__SaveSequence_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__SaveSequence_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__SaveSequence_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for SaveSequence_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for SaveSequence_Response where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/SaveSequence_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__SaveSequence_Response() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__DeleteSequence_Request() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__DeleteSequence_Request__init(msg: *mut DeleteSequence_Request) -> bool;
    fn gesture_management__srv__DeleteSequence_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DeleteSequence_Request>, size: usize) -> bool;
    fn gesture_management__srv__DeleteSequence_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DeleteSequence_Request>);
    fn gesture_management__srv__DeleteSequence_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DeleteSequence_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<DeleteSequence_Request>) -> bool;
}

// Corresponds to gesture_management__srv__DeleteSequence_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DeleteSequence_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub name: rosidl_runtime_rs::String,

}



impl Default for DeleteSequence_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__DeleteSequence_Request__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__DeleteSequence_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DeleteSequence_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__DeleteSequence_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__DeleteSequence_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__DeleteSequence_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DeleteSequence_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DeleteSequence_Request where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/DeleteSequence_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__DeleteSequence_Request() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__DeleteSequence_Response() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__DeleteSequence_Response__init(msg: *mut DeleteSequence_Response) -> bool;
    fn gesture_management__srv__DeleteSequence_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DeleteSequence_Response>, size: usize) -> bool;
    fn gesture_management__srv__DeleteSequence_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DeleteSequence_Response>);
    fn gesture_management__srv__DeleteSequence_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DeleteSequence_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<DeleteSequence_Response>) -> bool;
}

// Corresponds to gesture_management__srv__DeleteSequence_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DeleteSequence_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for DeleteSequence_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__DeleteSequence_Response__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__DeleteSequence_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DeleteSequence_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__DeleteSequence_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__DeleteSequence_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__DeleteSequence_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DeleteSequence_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DeleteSequence_Response where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/DeleteSequence_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__DeleteSequence_Response() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__ListSequences_Request() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__ListSequences_Request__init(msg: *mut ListSequences_Request) -> bool;
    fn gesture_management__srv__ListSequences_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ListSequences_Request>, size: usize) -> bool;
    fn gesture_management__srv__ListSequences_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ListSequences_Request>);
    fn gesture_management__srv__ListSequences_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ListSequences_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<ListSequences_Request>) -> bool;
}

// Corresponds to gesture_management__srv__ListSequences_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ListSequences_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for ListSequences_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__ListSequences_Request__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__ListSequences_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ListSequences_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ListSequences_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ListSequences_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ListSequences_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ListSequences_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ListSequences_Request where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/ListSequences_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__ListSequences_Request() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__ListSequences_Response() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__ListSequences_Response__init(msg: *mut ListSequences_Response) -> bool;
    fn gesture_management__srv__ListSequences_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ListSequences_Response>, size: usize) -> bool;
    fn gesture_management__srv__ListSequences_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ListSequences_Response>);
    fn gesture_management__srv__ListSequences_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ListSequences_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<ListSequences_Response>) -> bool;
}

// Corresponds to gesture_management__srv__ListSequences_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ListSequences_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub sequences_json: rosidl_runtime_rs::String,

}



impl Default for ListSequences_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__ListSequences_Response__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__ListSequences_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ListSequences_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ListSequences_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ListSequences_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__ListSequences_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ListSequences_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ListSequences_Response where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/ListSequences_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__ListSequences_Response() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__GetReplayStatus_Request() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__GetReplayStatus_Request__init(msg: *mut GetReplayStatus_Request) -> bool;
    fn gesture_management__srv__GetReplayStatus_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetReplayStatus_Request>, size: usize) -> bool;
    fn gesture_management__srv__GetReplayStatus_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetReplayStatus_Request>);
    fn gesture_management__srv__GetReplayStatus_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetReplayStatus_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<GetReplayStatus_Request>) -> bool;
}

// Corresponds to gesture_management__srv__GetReplayStatus_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetReplayStatus_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for GetReplayStatus_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__GetReplayStatus_Request__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__GetReplayStatus_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetReplayStatus_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__GetReplayStatus_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__GetReplayStatus_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__GetReplayStatus_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetReplayStatus_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetReplayStatus_Request where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/GetReplayStatus_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__GetReplayStatus_Request() }
  }
}


#[link(name = "gesture_management__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__GetReplayStatus_Response() -> *const std::ffi::c_void;
}

#[link(name = "gesture_management__rosidl_generator_c")]
extern "C" {
    fn gesture_management__srv__GetReplayStatus_Response__init(msg: *mut GetReplayStatus_Response) -> bool;
    fn gesture_management__srv__GetReplayStatus_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetReplayStatus_Response>, size: usize) -> bool;
    fn gesture_management__srv__GetReplayStatus_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetReplayStatus_Response>);
    fn gesture_management__srv__GetReplayStatus_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetReplayStatus_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<GetReplayStatus_Response>) -> bool;
}

// Corresponds to gesture_management__srv__GetReplayStatus_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetReplayStatus_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub status_json: rosidl_runtime_rs::String,

}



impl Default for GetReplayStatus_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !gesture_management__srv__GetReplayStatus_Response__init(&mut msg as *mut _) {
        panic!("Call to gesture_management__srv__GetReplayStatus_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetReplayStatus_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__GetReplayStatus_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__GetReplayStatus_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { gesture_management__srv__GetReplayStatus_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetReplayStatus_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetReplayStatus_Response where Self: Sized {
  const TYPE_NAME: &'static str = "gesture_management/srv/GetReplayStatus_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__gesture_management__srv__GetReplayStatus_Response() }
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


