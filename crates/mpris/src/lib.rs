//! # mpris
//! `mpris` tracks and controls media players on GNU/Linux desktops that implement the
//! [MPRIS D-Bus Interface Specification](https://specifications.freedesktop.org/mpris/latest/).
//!
//! [`MprisService`] watches the session bus for players. Each player is exposed as a
//! [`PlayerHandle`], whose state is kept in sync with the player and exposed as observable
//! [properties](PlayerHandleProperties).
//!
//! ## Example
//! ```rust,no_run
//! use mpris::MprisService;
//!
//! # let rt = tokio::runtime::Runtime::new().unwrap();
//! # rt.block_on(async {
//! let service = MprisService::new();
//! service.run().await.unwrap();
//!
//! for player in service.players() {
//!     let identity = player.properties.identity.read(|v| v.clone());
//!     let title = player.properties.metadata.read(|m| m.title.clone());
//!     println!("{identity} is playing {title:?}");
//! }
//!
//! service.events.player_added.connect(|player| {
//!     player.properties.playback_status.changed.connect(|status| {
//!         println!("Playback status changed: {status}");
//!     });
//! });
//!
//! service.events.player_removed.connect(|player| {
//!     println!("Player closed: {}", player.properties.identity.read(|v| v.clone()));
//! });
//! # });
//! ```

#![warn(missing_docs)]

mod dbus;
mod error;
mod file_utils;
mod metadata;
mod playback_status;
mod player;
mod private_prelude;
mod service;

pub use error::{Error, Result};
pub use metadata::Metadata;
pub use playback_status::{LoopStatus, PlaybackStatus};
pub use player::{PlayerHandle, PlayerHandleEvents, PlayerHandleProperties};
pub use service::{MprisService, MprisServiceEvents};

#[cfg(test)]
mod test_utils;
