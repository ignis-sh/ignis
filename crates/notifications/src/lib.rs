//! # notifications
//! `notifications` provides a notification daemon which receives and manages notifications sent by
//! applications on GNU/Linux desktops that follow XDG Desktop Notifications Specification.
//!
//! ## Example
//! ```rust
//! use notifications::{NotificationService, Event};
//! use tokio::sync::mpsc;
//!
//! # let rt = tokio::runtime::Runtime::new().unwrap();
//! # rt.block_on(async {
//!
//! let service = NotificationService::new(None).unwrap();
//! service.run().await.unwrap();
//!
//! // listen for events
//! let mut rx = service.subscribe();
//! tokio::spawn(async move {
//!     while let Some(msg) = rx.recv().await.ok() {
//!         match msg {
//!            Event::Notified {id, notification, replace} => println!("New
//!            notification! id: {}, summary: {}, replaces old one: {}", id, notification.summary(),
//!            replace),
//!            Event::NotificationClosed {id, reason} => println!("notificaiton
//!            closed id: {}, reason: {:?}", id, reason),
//!         }
//!     }
//! });
//! # });
//!
//! ```

#![warn(missing_docs)]

mod action;
mod close_reason;
mod data;
mod dbus;
mod error;
mod event;
mod file_utils;
mod notification;
mod private_prelude;
mod service;
mod settings;
mod urgency;

pub use action::ActionHandle;
pub use close_reason::CloseReason;
pub use error::{Error, Result};
pub use event::Event;
pub use notification::NotificationHandle;
pub use service::NotificationService;
pub use settings::Settings;
pub use urgency::Urgency;
