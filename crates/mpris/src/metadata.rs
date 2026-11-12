use std::collections::HashMap;

/// Metadata of the current track.
///
/// Fields are parsed from the
/// [MPRIS metadata](https://specifications.freedesktop.org/mpris/latest/Track_List_Interface.html#Mapping:Metadata_Map)
/// reported by the player. A field is `None` if the player doesn't provide it.
#[derive(Clone, Default)]
pub struct Metadata {
    /// The unique identifier of the track within the context of the player's track list.
    ///
    /// Pass it to [`set_position`].
    pub track_id: Option<String>,

    /// The duration of the track in microseconds.
    pub length: Option<i64>,

    /// The location of an image representing the track or album, as a URI.
    ///
    /// See also `cached_cover_art` of the player, which provides a local copy of the image.
    pub art_url: Option<String>,

    /// The album name.
    pub album: Option<String>,

    /// The album artist(s).
    pub album_artist: Option<String>,

    /// The track artist(s).
    pub artist: Option<String>,

    /// The track lyrics.
    pub as_text: Option<String>,

    /// The speed of the music, in beats per minute.
    pub audio_bpm: Option<String>,

    /// An automatically-generated rating, based on things such as how often it has been played.
    ///
    /// It is in the range from 0.0 to 1.0.
    pub auto_rating: Option<String>,

    /// A (list of) freeform comment(s).
    pub comment: Option<String>,

    /// The composer(s) of the track.
    pub composer: Option<String>,

    /// When the track was created, as an ISO 8601 date.
    pub content_created: Option<String>,

    /// The disc number on the album that this track is from.
    pub disc_number: Option<String>,

    /// When the track was first played, as an ISO 8601 date.
    pub first_used: Option<String>,

    /// The genre(s) of the track.
    pub genre: Option<String>,

    /// When the track was last played, as an ISO 8601 date.
    pub last_used: Option<String>,

    /// The lyricist(s) of the track.
    pub lyricist: Option<String>,

    /// The track title.
    pub title: Option<String>,

    /// The track number on the album disc.
    pub track_number: Option<u32>,

    /// The location of the media file, as a URI.
    pub url: Option<String>,

    /// The number of times the track has been played.
    pub use_count: Option<u32>,

    /// A user-specified rating, in the range from 0.0 to 1.0.
    pub user_rating: Option<f32>,
}

impl Metadata {
    pub(crate) fn from_map(map: HashMap<String, zbus::zvariant::OwnedValue>) -> Self {
        fn get_str(map: &HashMap<String, zbus::zvariant::OwnedValue>, key: &str) -> Option<String> {
            map.get(key)
                .map(|v| v.to_string().trim_matches('"').to_string())
        }

        Self {
            track_id: get_str(&map, "mpris:trackid"),
            length: get_str(&map, "mpris:length").and_then(|v| v.parse::<i64>().ok()),
            art_url: get_str(&map, "mpris:artUrl"),

            album: get_str(&map, "xesam:album"),
            album_artist: get_str(&map, "xesam:albumArtist"),
            artist: get_str(&map, "xesam:artist"),
            as_text: get_str(&map, "xesam:asText"),
            audio_bpm: get_str(&map, "xesam:audioBPM"),
            auto_rating: get_str(&map, "xesam:autoRating"),
            comment: get_str(&map, "xesam:comment"),
            composer: get_str(&map, "xesam:composer"),

            content_created: get_str(&map, "xesam:contentCreated"),
            disc_number: get_str(&map, "xesam:discNumber"),
            first_used: get_str(&map, "xesam:firstUsed"),
            genre: get_str(&map, "xesam:genre"),

            last_used: get_str(&map, "xesam:lastUsed"),
            lyricist: get_str(&map, "xesam:lyricist"),
            title: get_str(&map, "xesam:title"),
            track_number: get_str(&map, "xesam:trackNumber").and_then(|v| v.parse::<u32>().ok()),
            url: get_str(&map, "xesam:url"),
            use_count: get_str(&map, "xesam:useCount").and_then(|v| v.parse::<u32>().ok()),
            user_rating: get_str(&map, "xesam:userRating").and_then(|v| v.parse::<f32>().ok()),
        }
    }
}

impl From<HashMap<String, zbus::zvariant::OwnedValue>> for Metadata {
    fn from(value: HashMap<String, zbus::zvariant::OwnedValue>) -> Self {
        Self::from_map(value)
    }
}
