use crate::locale::SystemLocale;
use crate::private_prelude::*;
use ignis_events::Event;
use notify::{EventKind, INotifyWatcher, RecursiveMode, Watcher};
use nucleo_matcher::{Config, Matcher, Utf32Str};
use std::sync::{Mutex, mpsc};
use std::thread;
use std::{collections::HashMap, env, fs, path::PathBuf, sync::RwLock};

pub(crate) struct ApplicationServiceInner {
    applications: RwLock<HashMap<String, Arc<DesktopApp>>>,
    watcher: RwLock<Option<INotifyWatcher>>,
    app_dirs: Vec<PathBuf>,
    pub(crate) locale: SystemLocale,
    matcher: Mutex<Matcher>,
}

/// A service to access desktop applications.
#[derive(Clone)]
pub struct ApplicationService {
    pub(crate) inner: Arc<ApplicationServiceInner>,

    /// Emitted when the list of installed applications changed.
    ///
    /// This can occur, for example, when an application is installed or removed from the system.
    pub on_apps_refreshed: Event<()>,
}

impl ApplicationService {
    /// Creates a new instance.
    ///
    /// It loads all application entries from `XDG_DATA_DIRS` and gets the system locale.
    pub fn new() -> Self {
        Self::new_with_env(
            env::var_os("XDG_DATA_DIRS")
                .into_iter()
                .flat_map(|value| env::split_paths(&value).collect::<Vec<_>>())
                .map(|path| path.join("applications"))
                .collect(),
            ["LC_MESSAGES", "LC_ALL", "LANG"]
                .iter()
                .find_map(|name| env::var(name).ok())
                .unwrap_or_default()
                .as_ref(),
        )
    }

    pub(crate) fn new_with_env(app_dirs: Vec<PathBuf>, locale_string: &str) -> Self {
        Self {
            inner: Arc::new(ApplicationServiceInner {
                applications: RwLock::new(Self::init_apps(&app_dirs)),
                watcher: RwLock::new(None),
                app_dirs,
                locale: SystemLocale::new(locale_string),
                matcher: Mutex::new(Matcher::new(Config::DEFAULT)),
            }),
            on_apps_refreshed: Event::new(),
        }
    }

    /// Starts watching for changes in application entries. Re-initializes apps if a change occurs.
    ///
    /// # Errors
    /// `Error::NotifyError`
    pub fn watch(&self) -> Result<()> {
        let (tx, rx) = mpsc::channel();

        let mut watcher = notify::recommended_watcher(tx)?;

        for path in &self.inner.app_dirs {
            if path.exists() {
                watcher.watch(path, RecursiveMode::NonRecursive)?;
            };
        }

        *self.inner.watcher.write().unwrap() = Some(watcher);

        let service = self.clone();

        thread::spawn(move || {
            fn refresh(service: ApplicationService) {
                *service.inner.applications.write().unwrap() =
                    ApplicationService::init_apps(&service.inner.app_dirs);

                service.on_apps_refreshed.emit(&());

                tracing::debug!("Apps are refreshed");
            }

            for res in rx {
                let service = service.clone();
                match res {
                    Ok(event) => {
                        if let EventKind::Modify(_) = event.kind {
                            refresh(service)
                        }
                    }
                    Err(e) => {
                        tracing::warn!("Watch error: {}", e)
                    }
                }
            }
        });

        Ok(())
    }

    fn init_apps(app_dirs: &[PathBuf]) -> HashMap<String, Arc<DesktopApp>> {
        app_dirs
            .iter()
            .filter_map(|dir| fs::read_dir(dir).ok())
            .flatten()
            .filter_map(|entry| entry.ok())
            .filter(|entry| entry.file_name().to_string_lossy().ends_with(".desktop"))
            .filter_map(|entry| {
                DesktopApp::new(
                    entry.file_name().to_string_lossy().replace(".desktop", ""),
                    fs::read_to_string(entry.path()).ok()?,
                )
            })
            .map(|app| (app.app_id.clone(), Arc::new(app)))
            .fold(HashMap::new(), |mut map, (app_id, app)| {
                // use the first appearance of the desktop file
                map.entry(app_id).or_insert(app);
                map
            })
    }

    /// Returns a list of applications.
    pub fn apps(&self) -> Vec<DesktopAppHandle> {
        self.inner
            .applications
            .read()
            .unwrap()
            .values()
            .map(|app| DesktopAppHandle {
                inner: app.clone(),
                service: self.clone(),
            })
            .collect()
    }

    /// Returns an application by its ID, or `None` if it is not found.
    pub fn app_by_id(&self, app_id: &str) -> Option<DesktopAppHandle> {
        self.inner
            .applications
            .read()
            .unwrap()
            .get(app_id)
            .map(|app| DesktopAppHandle {
                inner: app.clone(),
                service: self.clone(),
            })
    }

    /// Fuzzily search through the application entries by provided application name.
    pub fn search_by_name(&self, query: &str) -> Vec<DesktopAppHandle> {
        let mut query_buf = Vec::new();
        let needle = Utf32Str::new(query, &mut query_buf);

        let mut results = Vec::new();

        for app in self.apps() {
            let mut app_buf = Vec::new();
            let name = app.name();
            let haystack = Utf32Str::new(&name, &mut app_buf);

            if let Some(score) = self
                .inner
                .matcher
                .lock()
                .unwrap()
                .fuzzy_match(haystack, needle)
            {
                results.push((app, score))
            }
        }

        results.sort_unstable_by_key(|(_, score)| std::cmp::Reverse(*score));

        results.into_iter().map(|(handle, _)| handle).collect()
    }
}

impl Default for ApplicationService {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use tempfile::TempDir;

    use super::*;
    use fake::Fake;
    use fake::faker::lorem::en::Sentence;
    use tracing_subscriber::EnvFilter;
    use uuid::Uuid;

    struct TestContext {
        tmp_dir: TempDir,
        apps_dir: PathBuf,
    }

    impl TestContext {
        fn new() -> Self {
            tracing_subscriber::fmt()
                .with_env_filter(EnvFilter::new("debug"))
                .try_init()
                .ok();

            let mut tmp_dir = TempDir::new().unwrap();

            if std::env::var_os("NO_TMP_CLEANUP")
                .unwrap_or_default()
                .to_string_lossy()
                == "1"
            {
                tmp_dir.disable_cleanup(true);
            }

            let apps_dir = tmp_dir.path().to_owned().join("applications");
            std::fs::create_dir(&apps_dir).unwrap();

            Self { tmp_dir, apps_dir }
        }

        fn add_random_entry(&self, application_type: &str, no_display: bool) {
            let name: String = Sentence(1..4).fake();
            let app_id = Uuid::new_v4().to_string();

            let contents = format!(
                r#"[Desktop Entry]
Name={}
Type={}
NoDisplay={}
                "#,
                name, application_type, no_display
            );

            std::fs::write(self.apps_dir.join(format!("{}.desktop", app_id)), contents).unwrap();
        }

        fn add_app_entry(&self, name: &str) {
            let app_id = Uuid::new_v4().to_string();
            let contents = format!(
                r#"[Desktop Entry]
Name={}
Type=Application
                "#,
                name
            );

            std::fs::write(self.apps_dir.join(format!("{}.desktop", app_id)), contents).unwrap();
        }

        fn init_service(&self) -> ApplicationService {
            ApplicationService::new_with_env(
                vec![self.tmp_dir.path().to_owned().join("applications")],
                "",
            )
        }
    }

    #[test]
    fn test_new() {
        let ctx = TestContext::new();
        let service = ctx.init_service();

        assert_eq!(service.apps().len(), 0);
    }

    #[test]
    fn test_apps() {
        let ctx = TestContext::new();
        for _ in 0..10 {
            ctx.add_random_entry("Application", false);
        }

        for _ in 0..5 {
            ctx.add_random_entry("Link", false);
        }

        ctx.add_random_entry("Application", true);

        let service = ctx.init_service();

        assert_eq!(service.apps().len(), 10);
    }

    #[test]
    fn test_watch() {
        let ctx = TestContext::new();
        ctx.add_random_entry("Application", false);
        let service = ctx.init_service();

        assert_eq!(service.apps().len(), 1);

        service.watch().unwrap();
        ctx.add_random_entry("Application", false);

        thread::sleep(Duration::from_millis(500));
        assert_eq!(service.apps().len(), 2);
    }

    #[test]
    fn test_search() {
        let ctx = TestContext::new();
        ctx.add_app_entry("Firefox");
        ctx.add_app_entry("Steam");
        ctx.add_app_entry("Ignis");

        let service = ctx.init_service();

        assert_eq!(
            service.search_by_name("Firefox").get(0).unwrap().name(),
            "Firefox"
        );

        assert_eq!(
            service.search_by_name("fire").get(0).unwrap().name(),
            "Firefox"
        );

        assert_eq!(service.search_by_name("sm").get(0).unwrap().name(), "Steam");

        assert_eq!(
            service.search_by_name("igns").get(0).unwrap().name(),
            "Ignis"
        );
    }

    #[test]
    fn test_on_apps_refreshed() {
        let received = Arc::new(Mutex::new(false));

        let ctx = TestContext::new();
        let service = ctx.init_service();
        service.watch().unwrap();

        let received_clone = received.clone();

        service.on_apps_refreshed.connect(move |_| {
            *received_clone.lock().unwrap() = true;
        });

        ctx.add_app_entry("Asd");

        std::thread::sleep(std::time::Duration::from_secs(1));

        assert_eq!(*received.lock().unwrap(), true);
    }
}
