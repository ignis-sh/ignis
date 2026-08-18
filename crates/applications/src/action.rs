use configparser::ini::Ini;

use crate::private_prelude::*;

pub(crate) struct Action {
    id: String,
    ini: Ini,
    name: String,
}

impl Action {
    fn get_section(id: &str) -> String {
        format!("Desktop Action {}", id)
    }

    pub(crate) fn new(id: String, ini: Ini) -> Option<Self> {
        Some(Self {
            name: ini.get(&Self::get_section(&id), "Name")?,
            id,
            ini,
        })
    }
}

pub struct ActionHandle {
    pub(crate) inner: Arc<Action>,
    pub(crate) service: ApplicationService,
}

impl ActionHandle {
    fn get_section(&self) -> String {
        Action::get_section(&self.inner.id)
    }

    fn get_value(&self, key: &str) -> Option<String> {
        self.inner.ini.get(&self.get_section(), key)
    }

    fn get_value_locale(&self, key: &str) -> Option<String> {
        utils::get_locale_string(
            &self.inner.ini,
            &self.get_section(),
            key,
            &self.service.inner.locale,
        )
    }

    pub fn name(&self) -> String {
        self.inner.name.clone()
    }

    pub fn name_locale(&self) -> String {
        self.get_value_locale("Name").unwrap_or_else(|| self.name())
    }

    pub fn icon(&self) -> Option<String> {
        self.get_value("Icon")
    }

    pub fn icon_locale(&self) -> Option<String> {
        self.get_value_locale("Icon").or_else(|| self.icon())
    }

    pub fn exec(&self) -> Option<String> {
        self.get_value("Exec")
    }

    fn terminal(&self) -> bool {
        self.inner
            .ini
            .getbool("Desktop Entry", "Terminal")
            .ok()
            .flatten()
            .unwrap_or(false)
    }

    pub fn launch(&self) -> Result<()> {
        utils::launch_from_exec_string(self.exec(), self.terminal())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use configparser::ini::Ini;

    fn new_handle(id: &str, contents: String, locale: &str) -> ActionHandle {
        let mut ini = Ini::new();
        ini.read(contents).unwrap();

        ActionHandle {
            inner: Arc::new(Action::new(String::from(id), ini).unwrap()),
            service: ApplicationService::new_with_env(vec![], locale),
        }
    }
    #[test]
    fn test_properties() {
        let contents = String::from(
            r#"[Desktop Action Meow]
Name=Meow
Name[en]=Meow english
Icon=some-icon
Exec=ls"#,
        );

        let handle = new_handle("Meow", contents, "en");

        assert_eq!(handle.name(), "Meow");
        assert_eq!(handle.name_locale(), "Meow english");
        assert_eq!(handle.icon().unwrap(), "some-icon");
        assert_eq!(handle.exec().unwrap(), "ls");
    }

    #[test]
    #[should_panic]
    fn test_invalid() {
        // entry without name
        let contents = String::from(
            r#"[Desktop Action Meow]
Icon=some-icon
Exec=ls"#,
        );

        new_handle("Meow", contents, "");
    }
}
