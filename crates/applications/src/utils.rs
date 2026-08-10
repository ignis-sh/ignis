use configparser::ini::Ini;

use crate::{locale::SystemLocale, private_prelude::*};

pub(crate) fn run_from_exec_string(exec_string: Option<String>) -> Result<()> {
    let args: Vec<String> = exec_string
        .ok_or(Error::ExecEmpty)?
        .split(" ")
        .map(String::from)
        .collect();

    let executable = args.get(0).ok_or(Error::ExecEmpty)?;
    tokio::process::Command::new(executable)
        .args(&args[1..])
        .spawn()?;

    Ok(())
}

pub(crate) fn get_locale_string(
    ini: &Ini,
    section: &str,
    key: &str,
    locale: &SystemLocale,
) -> Option<String> {
    let get_value = |locale: String| ini.get(section, &format!("{}[{}]", key, locale));

    get_value(locale.lang_country_modifier().unwrap_or_default())
        .or_else(|| get_value(locale.lang_country().unwrap_or_default()))
        .or_else(|| get_value(locale.lang_modifier().unwrap_or_default()))
        .or_else(|| get_value(locale.lang_only()))
        .or_else(|| ini.get(section, key))
}
