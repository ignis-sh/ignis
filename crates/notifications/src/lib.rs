//! # notifications
//! `notifications` provides a notification daemon which receives and manages notifications sent by
//! applications on GNU/Linux desktops that follow XDG Desktop Notifications Specification.
//!
//! ## Example
//! ```rust
//! use notifications::NotificationService;
//!
//! # let rt = tokio::runtime::Runtime::new().unwrap();
//! # rt.block_on(async {
//!
//! let service = NotificationService::new(None).unwrap();
//! service.run().await.unwrap();
//!
//! service.on_notified.connect(|(id, notification, replace)| println!("New
//! notification! id: {}, summary: {}, replaces old one: {}", id, notification.summary(), replace));
//!
//! service.on_notification_closed.connect(|(id, reason)| println!("Notification closed! id: {},
//! reason: {:?}", id, reason));
//! # });
//!
//! ```

#![warn(missing_docs)]

mod action;
mod close_reason;
mod data;
mod dbus;
mod error;
mod file_utils;
mod notification;
mod private_prelude;
mod service;
mod settings;
mod urgency;

pub use action::ActionHandle;
pub use close_reason::CloseReason;
pub use error::{Error, Result};
pub use notification::NotificationHandle;
pub use service::NotificationService;
pub use settings::Settings;
pub use urgency::Urgency;
