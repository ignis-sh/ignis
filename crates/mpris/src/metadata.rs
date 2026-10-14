use std::collections::HashMap;

#[derive(Clone, Default)]
pub struct Metadata {
    pub track_id: Option<String>,
    pub length: Option<i64>,
    pub art_url: Option<String>,
    pub album: Option<String>,
    pub album_artist: Option<String>,
    pub artist: Option<String>,
    pub as_text: Option<String>,
    pub audio_bpm: Option<String>,
    pub auto_rating: Option<String>,
    pub comment: Option<String>,
    pub composer: Option<String>,
    pub content_created: Option<String>,
    pub disc_number: Option<String>,
    pub first_used: Option<String>,
    pub genre: Option<String>,
    pub last_used: Option<String>,
    pub lyricist: Option<String>,
    pub title: Option<String>,
    pub track_number: Option<u32>,
    pub url: Option<String>,
    pub use_count: Option<u32>,
    pub user_rating: Option<f32>,
}

impl Metadata {
    pub(crate) fn from_map(map: HashMap<String, zbus::zvariant::OwnedValue>) -> Self {
        fn get_str(map: &HashMap<String, zbus::zvariant::OwnedValue>, key: &str) -> Option<String> {
            map.get(key)
                .and_then(|v| Some(v.to_string().trim_matches('"').to_string()))
        }

        Self {
            track_id: get_str(&map, "mpris:trackId"),
            length: get_str(&map, "mpris:length").and_then(|v| v.parse::<i64>().ok()),
            art_url: get_str(&map, "mpris:artUrl"),

            album: get_str(&map, "xesam:album"),
            album_artist: get_str(&map, "xesam:album_artist"),
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
            use_count: get_str(&map, "xesam:trackNumber").and_then(|v| v.parse::<u32>().ok()),
            // user_rating: downcast::<f32>(&map, "xesam:userRating"),
            user_rating: None,
        }
    }
}

impl From<HashMap<String, zbus::zvariant::OwnedValue>> for Metadata {
    fn from(value: HashMap<String, zbus::zvariant::OwnedValue>) -> Self {
        Self::from_map(value)
    }
}
