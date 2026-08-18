use crate::{locale::SystemLocale, private_prelude::*};
use configparser::ini::Ini;
use std::process::{Command, Stdio};

fn parse_exec(input: &str) -> Result<(String, Vec<String>)> {
    let args: Vec<String> = input
        .split(" ")
        .map(String::from)
        .filter(|s| !s.starts_with("%")) // TODO: support field codes
        .collect();

    let executable = args.get(0).ok_or(Error::ExecEmpty)?.to_owned();

    Ok((executable, args[1..].to_owned()))
}

pub(crate) fn launch_from_exec_string(exec_string: Option<String>) -> Result<()> {
    let (executable, args) = parse_exec(&exec_string.ok_or(Error::ExecEmpty)?)?;

    Command::new(executable)
        .args(&args)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
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

#[cfg(test)]
mod tests {
    use crate::utils::parse_exec;

    #[test]
    fn test_parse_exec() {
        let string = "my-bin -a --test %F %U";
        assert_eq!(
            parse_exec(string).unwrap(),
            (
                "my-bin".to_string(),
                vec!["-a".to_string(), "--test".to_string()]
            )
        );
    }
}
