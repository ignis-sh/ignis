// https://specifications.freedesktop.org/mpris/latest/Player_Interface.html#Enum:Playback_Status
//

#[derive(Copy, Clone)]
pub enum PlaybackStatus {
    Playing,
    Paused,
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

impl Into<String> for PlaybackStatus {
    fn into(self) -> String {
        String::from(match self {
            Self::Playing => "Playing",
            Self::Paused => "Paused",
            Self::Stopped => "Stopped",
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

#[derive(Copy, Clone)]
pub enum LoopStatus {
    None,
    Track,
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
