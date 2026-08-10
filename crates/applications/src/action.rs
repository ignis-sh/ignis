use configparser::ini::Ini;

use crate::private_prelude::*;

pub(crate) struct Action {
    name: String,
    icon: Option<String>,
    exec: Option<String>,
}

impl Action {
    fn get_value(id: &str, ini: &Ini, key: &str) -> Option<String> {
        ini.get(&format!("Desktop Action {}", id), key)
    }

    pub(crate) fn new(id: &str, ini: &Ini) -> Option<Self> {
        Some(Self {
            name: Self::get_value(id, ini, "Name")?,
            icon: Self::get_value(id, ini, "Icon"),
            exec: Self::get_value(id, ini, "Exec"),
        })
    }
}

pub struct ActionHandle {
    pub(crate) inner: Arc<Action>,
}

impl ActionHandle {
    pub fn name(&self) -> String {
        self.inner.name.clone()
    }

    pub fn icon(&self) -> Option<String> {
        self.inner.icon.clone()
    }

    pub fn exec(&self) -> Option<String> {
        self.inner.exec.clone()
    }

    pub fn run(&self) -> Result<()> {
        utils::run_from_exec_string(self.exec())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use configparser::ini::Ini;

    fn new_handle(id: &str, contents: String) -> ActionHandle {
        let mut ini = Ini::new();
        ini.read(contents).unwrap();

        ActionHandle {
            inner: Arc::new(Action::new(id, &ini).unwrap()),
        }
    }
    #[test]
    fn test_properties() {
        let contents = String::from(
            r#"[Desktop Action Meow]
Name=Meow
Icon=some-icon
Exec=ls"#,
        );

        let handle = new_handle("Meow", contents);

        assert_eq!(handle.name(), "Meow");
        assert_eq!(handle.icon().unwrap(), "some-icon");
        assert_eq!(handle.exec().unwrap(), "ls");
    }
}
