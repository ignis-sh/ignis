use crate::private_prelude::*;
use std::collections::BTreeMap;
use std::fs;
use std::sync::RwLock;

#[derive(Serialize, Deserialize, Default)]
struct ServiceDataInner {
    counter: u32,
    notifications: BTreeMap<u32, Arc<Notification>>,
}

#[derive(Default)]
pub(crate) struct ServiceData {
    inner: RwLock<ServiceDataInner>,
    file_path: Option<PathBuf>, // if None - file I/O is disabled
}

impl ServiceData {
    pub(crate) fn new(cache_dir: Option<PathBuf>) -> Result<Self> {
        let file_path = file_utils::get_history_file_path(cache_dir)?;

        let inner = match fs::read_to_string(&file_path) {
            Ok(s) => serde_json::from_str(&s)?,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => ServiceDataInner::default(),
            Err(e) => return Err(e.into()),
        };

        Ok(Self {
            inner: RwLock::new(inner),
            file_path: Some(file_path),
        })
    }

    pub(crate) fn new_in_memory() -> Self {
        Self::default()
    }

    pub(crate) fn add_notification(
        &self,
        id: u32,
        new_notification: Arc<Notification>,
        replace: bool,
    ) -> Result<()> {
        if !replace {
            self.inner
                .write()
                .unwrap()
                .notifications
                .insert(id, new_notification);
        } else {
            if let Some(old_notification) = self.inner.write().unwrap().notifications.get_mut(&id) {
                *old_notification = new_notification;
            }
        }

        self.save_to_file()?;

        Ok(())
    }

    pub fn remove_notification(&self, id: u32) -> Result<()> {
        self.inner
            .write()
            .unwrap()
            .notifications
            .remove(&id)
            .ok_or_else(|| Error::NotificationNotFound(id))?;

        self.save_to_file()?;
        Ok(())
    }

    pub fn clear(&self) -> Result<()> {
        {
            let mut inner = self.inner.write().unwrap();
            inner.notifications.clear();
            inner.counter = 0;
        }
        self.save_to_file()?;
        Ok(())
    }

    pub fn get_notifications(&self) -> BTreeMap<u32, Arc<Notification>> {
        self.inner.read().unwrap().notifications.clone()
    }

    pub fn increment_counter(&self) -> u32 {
        let mut guard = self.inner.write().unwrap();
        guard.counter += 1;
        guard.counter
    }

    fn save_to_file(&self) -> Result<()> {
        if let Some(file_path) = self.file_path.clone() {
            let json_str = serde_json::to_string_pretty(&*self.inner.read().unwrap())?;
            fs::write(&file_path, json_str)?;
        };

        Ok(())
    }
}
