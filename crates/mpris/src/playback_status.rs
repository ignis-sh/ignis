// https://specifications.freedesktop.org/mpris/latest/Player_Interface.html#Enum:Playback_Status
//

/// The playback state of a player.
///
/// Unknown values reported by a player are treated as [`PlaybackStatus::Stopped`].
#[derive(Copy, Clone)]
pub enum PlaybackStatus {
    /// A track is currently playing.
    Playing,

    /// A track is currently paused.
    Paused,

    /// There is no track currently playing.
    Stopped,
}

impl From<&str> for PlaybackStatus {
    fn from(value: &str) -> Self {
        match value {
            "Playing" => Self::Playing,
            "Paused" => Self::Paused,
            "Stopped" => Self::Stopped,
            _ => Self::Stopped,
        }
    }
}

impl From<String> for PlaybackStatus {
    fn from(value: String) -> Self {
        Self::from(value.as_str())
    }
}

impl From<PlaybackStatus> for String {
    fn from(value: PlaybackStatus) -> String {
        String::from(match value {
            PlaybackStatus::Playing => "Playing",
            PlaybackStatus::Paused => "Paused",
            PlaybackStatus::Stopped => "Stopped",
        })
    }
}

impl std::fmt::Display for PlaybackStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(match self {
            Self::Playing => "Playing",
            Self::Paused => "Paused",
            Self::Stopped => "Stopped",
        })
    }
}

/// The looping behavior of a player.
///
/// Unknown values reported by a player are treated as [`LoopStatus::None`].
#[derive(Copy, Clone)]
pub enum LoopStatus {
    /// The playback will stop when there are no more tracks to play.
    None,

    /// The current track will start again from the beginning once it has finished playing.
    Track,

    /// The playback loops through a list of tracks.
    Playlist,
}

impl From<&str> for LoopStatus {
    fn from(value: &str) -> Self {
        match value {
            "None" => Self::None,
            "Track" => Self::Track,
            "Playlist" => Self::Playlist,
            _ => Self::None,
        }
    }
}

impl std::fmt::Display for LoopStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(match self {
            Self::None => "None",
            Self::Track => "Track",
            Self::Playlist => "Playlist",
        })
    }
}

impl From<String> for LoopStatus {
    fn from(value: String) -> Self {
        Self::from(value.as_str())
    }
}
