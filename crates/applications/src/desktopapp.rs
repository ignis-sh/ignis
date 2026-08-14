use crate::private_prelude::*;
use configparser::ini::Ini;

fn string_to_vec(value: Option<String>) -> Vec<String> {
    value
        .map(|value| {
            value
                .split(";")
                .filter(|s| !s.is_empty())
                .map(String::from)
                .collect()
        })
        .unwrap_or_default()
}
pub(crate) struct DesktopApp {
    pub(crate) app_id: String,
    pub(crate) ini: Ini,
    pub(crate) actions: Vec<Arc<Action>>,
    pub(crate) name: String,
}

impl DesktopApp {
    pub(crate) fn new(app_id: String, contents: String) -> Option<Self> {
        let mut ini = Ini::new();
        ini.set_comment_symbols(&['#']);

        ini.read(contents).ok()?;

        if ini
            .getbool("Desktop Entry", "NoDisplay")
            .unwrap_or_else(|_| Some(false))
            .unwrap_or(false)
        {
            return None;
        }

        if ini.get("Desktop Entry", "Type")? != "Application" {
            return None;
        };

        let actions: Vec<Arc<Action>> = ini
            .get("Desktop Entry", "Actions")
            .and_then(|a| {
                Some(
                    a.split(";")
                        .into_iter()
                        .filter(|a| !a.is_empty())
                        .filter_map(|id| Action::new(String::from(id), ini.clone()))
                        .map(|action| Arc::new(action))
                        .collect(),
                )
            })
            .unwrap_or_else(|| Vec::new());

        let name = ini.get("Desktop Entry", "Name")?;

        Some(Self {
            app_id,
            ini,
            actions,
            name,
        })
    }
}

#[derive(Clone)]
pub struct DesktopAppHandle {
    pub(crate) inner: Arc<DesktopApp>,
    pub(crate) service: ApplicationService,
}

impl DesktopAppHandle {
    fn get_value(&self, key: &str) -> Option<String> {
        self.inner.ini.get("Desktop Entry", key)
    }

    fn get_value_locale(&self, key: &str) -> Option<String> {
        // Locale matching with order:
        // lang_COUNTRY@MODIFIER - lang_COUNTRY@MODIFIER, lang_COUNTRY, lang@MODIFIER, lang, default value
        // lang_COUNTRY	- lang_COUNTRY, lang, default value
        // lang@MODIFIER - lang@MODIFIER, lang, default value
        // lang	- lang, default value
        //
        // See spec for more info: https://specifications.freedesktop.org/desktop-entry/latest/localized-keys.html

        utils::get_locale_string(
            &self.inner.ini,
            "Desktop Entry",
            key,
            &self.service.inner.locale,
        )
    }

    pub fn app_id(&self) -> String {
        self.inner.app_id.clone()
    }

    pub fn name(&self) -> String {
        self.inner.name.clone()
    }

    pub fn name_locale(&self) -> String {
        self.get_value_locale("Name").unwrap_or_else(|| self.name())
    }

    pub fn generic_name(&self) -> Option<String> {
        self.get_value("GenericName")
    }

    pub fn generic_name_locale(&self) -> Option<String> {
        self.get_value_locale("GenericName")
    }

    pub fn icon(&self) -> Option<String> {
        self.get_value("Icon")
    }

    pub fn icon_locale(&self) -> Option<String> {
        self.get_value_locale("Icon")
    }

    pub fn keywords(&self) -> Vec<String> {
        string_to_vec(self.get_value("Keywords"))
    }

    pub fn keywords_locale(&self) -> Vec<String> {
        string_to_vec(self.get_value_locale("Keywords"))
    }

    pub fn exec(&self) -> Option<String> {
        self.get_value("Exec")
    }

    pub fn terminal(&self) -> bool {
        self.get_value("Terminal")
            .and_then(|value| value.parse::<bool>().ok())
            .unwrap_or(false)
    }

    pub fn actions(&self) -> Vec<ActionHandle> {
        self.inner
            .actions
            .iter()
            .map(|action| ActionHandle {
                inner: action.clone(),
                service: self.service.clone(),
            })
            .collect()
    }

    pub fn run(&self) -> Result<()> {
        utils::run_from_exec_string(self.exec())
    }
}

#[cfg(test)]
mod tests {

    use super::*;

    fn new_handle(contents: String, locale: &str) -> DesktopAppHandle {
        DesktopAppHandle {
            inner: Arc::new(
                DesktopApp::new(String::from("com.example.program"), contents).unwrap(),
            ),
            service: ApplicationService::new_with_env(Vec::new(), locale),
        }
    }

    #[test]
    fn test_properties() {
        let contents = format!(
            r#"[Desktop Entry]
Name=Some Name
GenericName=This feels too generic
Icon=some-icon
Keywords=One;Two;Three;
Exec=do --this
Terminal=true
Type=Application
"#
        );

        let handle = new_handle(contents, "");
        assert_eq!(handle.name(), "Some Name");
        assert_eq!(handle.generic_name().unwrap(), "This feels too generic");
        assert_eq!(handle.icon().unwrap(), "some-icon");
        assert_eq!(handle.keywords(), vec!["One", "Two", "Three"]);
        assert_eq!(handle.exec().unwrap(), "do --this");
        assert_eq!(handle.terminal(), true);
    }

    #[test]
    fn test_locale() {
        let contents = String::from(
            r#"[Desktop Entry]
Name=Some Name
Name[en_US@Idk]=Lang Country Modifier
Name[en_US]=Lang Country
Name[en@Idk]=Lang Modifier
Name[en]=Lang Only
Type=Application
"#,
        );
        let handle = new_handle(contents.clone(), "en_US@Idk");

        assert_eq!(handle.name_locale(), "Lang Country Modifier");

        let handle = new_handle(contents.clone(), "en_US");
        assert_eq!(handle.name_locale(), "Lang Country");

        let handle = new_handle(contents.clone(), "en@Idk");
        assert_eq!(handle.name_locale(), "Lang Modifier");

        let handle = new_handle(contents.clone(), "en");
        assert_eq!(handle.name_locale(), "Lang Only");

        let handle = new_handle(contents, "invalid");
        assert_eq!(handle.name_locale(), "Some Name");

        let contents = String::from(
            r#"[Desktop Entry]
Name=Some Name
Type=Application
Name[en_US]=Lang Country
Name[en@Idk]=Lang Modifier
Name[en]=Lang Only
"#,
        );

        let handle = new_handle(contents.clone(), "en_US@Idk");

        assert_eq!(handle.name_locale(), "Lang Country");
    }

    #[test]
    fn test_actions() {
        let contents = String::from(
            r#"[Desktop Entry]
Name=Some Name
Type=Application
Actions=Meow;Open;Test

[Desktop Action Meow]
Name=Meow
Icon=some-icon
Exec=ls

[Desktop Action Open]
Name=Meow
Icon=some-icon
Exec=ls
"#,
        );

        let handle = new_handle(contents, "");

        assert_eq!(handle.actions().len(), 2);
    }

    #[tokio::test]
    async fn test_exec() {
        let contents = String::from(
            r#"[Desktop Entry]
Name=Some Name
Type=Application
Exec=ls
"#,
        );
        let handle = new_handle(contents, "");
        handle.run().unwrap();
    }
}
