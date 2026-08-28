//! # applications
//!
//! Access desktop application entries defined according to the [XDG Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry/latest).
//!
//! # Example
//! ```rust
//! use applications::ApplicationService;
//!
//! let service = ApplicationService::new();
//!
//! // Display names of all apps
//! for i in service.apps() {
//!     println!("{}", i.name())
//! }
//!
//! // Fuzzy search by name
//! // Best matches come first in the vector
//! let matches = service.search_by_name("firox");
//!
//!
//! if let Some(app) = matches.first() {
//!     // Launch application
//!     app.launch();
//!
//!     // Inspect actions
//!     for action in app.actions() {
//!         println!("{}", action.name());
//!
//!         // You can launch them too
//!         // action.launch()
//!     }
//! }
//!
//! ```
#![warn(missing_docs)]
mod action;
mod desktopapp;
mod error;
mod event;
mod locale;
mod private_prelude;
mod service;
mod utils;

pub use action::ActionHandle;
pub use desktopapp::DesktopAppHandle;
pub use error::{Error, Result};
pub use service::ApplicationService;
