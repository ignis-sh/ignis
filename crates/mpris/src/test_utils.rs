use fake::{Dummy, Fake, Faker};
use std::collections::HashMap;
#[cfg(test)]
use std::sync::Arc;
use std::sync::Mutex;
use zbus::{conn::Builder, interface, object_server::SignalEmitter};

#[derive(Default)]
pub struct TestMediaPlayer2Data {
    pub can_quit: bool,
    pub can_raise: bool,
    pub can_set_fullscreen: bool,
    pub desktop_entry: String,
    pub fullscreen: Mutex<bool>,
    pub has_track_list: bool,
    pub identity: String,
    pub supported_mime_types: Vec<String>,
    pub supported_uri_schemes: Vec<String>,
}

#[cfg(test)]
pub struct TestMediaPlayer2 {
    data: Arc<Mutex<TestMediaPlayer2Data>>,
}

#[interface(name = "org.mpris.MediaPlayer2")]
impl TestMediaPlayer2 {
    pub fn quit(&self) {}
    pub fn raise(&self) {}

    #[zbus(property)]
    pub fn can_quit(&self) -> bool {
        self.data.lock().unwrap().can_quit
    }

    #[zbus(property)]
    pub fn can_raise(&self) -> bool {
        self.data.lock().unwrap().can_raise
    }

    #[zbus(property)]
    pub fn can_set_fullscreen(&self) -> bool {
        self.data.lock().unwrap().can_set_fullscreen
    }

    #[zbus(property)]
    pub fn desktop_entry(&self) -> String {
        self.data.lock().unwrap().desktop_entry.clone()
    }

    #[zbus(property)]
    pub fn fullscreen(&self) -> bool {
        self.data.lock().unwrap().can_raise
    }
    #[zbus(property)]
    pub fn set_fullscreen(&self, value: bool) {
        *self.data.lock().unwrap().fullscreen.lock().unwrap() = value;
    }

    #[zbus(property)]
    pub fn has_track_list(&self) -> bool {
        self.data.lock().unwrap().has_track_list
    }

    #[zbus(property)]
    pub fn identity(&self) -> String {
        self.data.lock().unwrap().identity.clone()
    }

    #[zbus(property)]
    pub fn supported_mime_types(&self) -> Vec<String> {
        self.data.lock().unwrap().supported_mime_types.clone()
    }

    #[zbus(property)]
    pub fn supported_uri_schemes(&self) -> Vec<String> {
        self.data.lock().unwrap().supported_uri_schemes.clone()
    }
}

#[derive(Dummy)]
pub struct TestPlayer {
    pub can_control: bool,
    pub can_go_next: bool,
    pub can_go_previous: bool,
    pub can_pause: bool,
    pub can_play: bool,
    pub can_seek: bool,
    pub loop_status: Mutex<String>,
    pub maximum_rate: f64,
    pub minimum_rate: f64,
    pub metadata: HashMap<String, String>,
    pub playback_status: String,
    pub position: i64,
    pub rate: Mutex<f64>,
    pub shuffle: Mutex<bool>,
    pub volume: Mutex<f64>,
}

#[interface(name = "org.mpris.MediaPlayer2.Player")]
impl TestPlayer {
    pub fn next(&self) {}
    pub fn open_uri(&self, _uri: &str) {}
    pub fn pause(&self) {}
    pub fn play(&self) {}
    pub fn play_pause(&self) {}
    pub fn previous(&self) {}
    pub fn seek(&self, _offset: i64) {}
    pub fn set_position(&self, _track_id: String, _position: i64) {}
    pub fn stop(&self) {}

    #[zbus(signal)]
    pub async fn seeked(&self, _emitter: &SignalEmitter<'_>, position: i64) -> zbus::Result<()>;

    #[zbus(property)]
    pub fn can_control(&self) -> bool {
        self.can_control
    }
    #[zbus(property)]
    pub fn can_go_next(&self) -> bool {
        self.can_go_next
    }

    #[zbus(property)]
    pub fn can_go_previous(&self) -> bool {
        self.can_go_previous
    }

    #[zbus(property)]
    pub fn can_pause(&self) -> bool {
        self.can_pause
    }

    #[zbus(property)]
    pub fn can_play(&self) -> bool {
        self.can_play
    }

    #[zbus(property)]
    pub fn can_seek(&self) -> bool {
        self.can_seek
    }

    #[zbus(property)]
    pub fn loop_status(&self) -> String {
        self.loop_status.lock().unwrap().clone()
    }

    #[zbus(property)]
    pub fn set_loop_status(&self, value: &str) {
        *self.loop_status.lock().unwrap() = String::from(value);
    }

    #[zbus(property)]
    pub fn maximum_rate(&self) -> f64 {
        self.maximum_rate
    }

    #[zbus(property)]
    pub fn metadata(&self) -> std::collections::HashMap<String, String> {
        self.metadata.clone()
    }

    #[zbus(property)]
    pub fn minimum_rate(&self) -> f64 {
        self.minimum_rate
    }

    #[zbus(property)]
    pub fn playback_status(&self) -> String {
        self.playback_status.clone()
    }

    #[zbus(property)]
    pub fn position(&self) -> i64 {
        self.position
    }

    #[zbus(property)]
    pub fn rate(&self) -> f64 {
        *self.rate.lock().unwrap()
    }
    #[zbus(property)]
    pub fn set_rate(&self, value: f64) {
        *self.rate.lock().unwrap() = value;
    }

    #[zbus(property)]
    pub fn shuffle(&self) -> bool {
        *self.shuffle.lock().unwrap()
    }
    #[zbus(property)]
    pub fn set_shuffle(&self, value: bool) {
        *self.shuffle.lock().unwrap() = value;
    }

    #[zbus(property)]
    pub fn volume(&self) -> f64 {
        *self.volume.lock().unwrap()
    }

    #[zbus(property)]
    pub fn set_volume(&self, value: f64) {
        *self.volume.lock().unwrap() = value;
    }
}

pub struct TestContext {
    conns: Mutex<HashMap<String, zbus::Connection>>,
}

pub struct TestPlayerInfo {
    pub connection: zbus::Connection,
    pub media_player_data: Arc<Mutex<TestMediaPlayer2Data>>,
    pub name: String,
}

impl TestContext {
    pub async fn new() -> Self {
        Self {
            conns: Mutex::new(HashMap::new()),
        }
    }

    pub async fn run_player(&self) -> TestPlayerInfo {
        let codename: String = fake::faker::lorem::en::Word().fake();
        let media_player_data = Arc::new(Mutex::new(TestMediaPlayer2Data::default()));
        let player: TestPlayer = Faker.fake();

        let name = format!("org.mpris.MediaPlayer2.{}", codename);

        let connection = Builder::session()
            .unwrap()
            .name(name.clone())
            .unwrap()
            .serve_at(
                "/org/mpris/MediaPlayer2",
                TestMediaPlayer2 {
                    data: media_player_data.clone(),
                },
            )
            .unwrap()
            .serve_at("/org/mpris/MediaPlayer2", player)
            .unwrap()
            .build()
            .await
            .unwrap();

        self.conns
            .lock()
            .unwrap()
            .insert(name.clone(), connection.clone());

        TestPlayerInfo {
            connection,
            media_player_data,
            name,
        }
    }

    pub async fn drop_player(&self, name: &str) {
        let conn = self.conns.lock().unwrap().remove(name).unwrap();
        conn.release_name(name).await.unwrap();
    }
}
