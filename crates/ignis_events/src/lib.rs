//! # ignis_events
//!
//! `ignis_events` crate provides utilities to manage events and callbacks.
//!
//! It allows users to listen for events and execute the registered callbacks when an event occurs.
//!
//! ## Example
//! ```rust
//! use ignis_events::Event;
//!
//! struct MyService {
//!     on_something_happened: Event<u32>,
//! }
//!
//! impl MyService {
//!     fn new() -> Self {
//!         Self {
//!             on_something_happened: Event::<u32>::new(),
//!         }
//!     }
//! }
//!
//! let service = MyService::new();
//! let handle = service.on_something_happened.connect(|arg| {
//!     println!("Something happened");
//!     assert_eq!(*arg, 67);
//! });
//!
//! // NOTE: usually you must not emit events by yourself.
//! // It should be done by the struct owning the event.
//! service.on_something_happened.emit(&67);
//!
//! // Disconnect when you do not need to invoke this callback anymore
//! service.on_something_happened.disconnect(handle);
//! ```
#[warn(missing_docs)]
mod event;

pub use event::Event;
