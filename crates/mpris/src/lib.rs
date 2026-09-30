mod dbus;
mod error;
mod player;
mod private_prelude;
mod service;

pub use error::{Error, Result};
pub use player::PlayerHandle;
pub use service::MprisService;
