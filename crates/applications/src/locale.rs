pub(crate) struct SystemLocale {
    pub(crate) lang: String,
    pub(crate) country: Option<String>,
    pub(crate) modifier: Option<String>,
}

impl SystemLocale {
    pub(crate) fn new(input: &str) -> Self {
        let (base, modifier) = input
            .split_once('@')
            .map_or((input, None), |(a, b)| (a, Some(b.to_string())));

        let (base, _encoding) = base
            .split_once('.')
            .map_or((base, None), |(a, b)| (a, Some(b.to_string())));

        let (lang, country) = base
            .split_once('_')
            .map_or((base, None), |(a, b)| (a, Some(b.to_string())));

        Self {
            lang: lang.into(),
            country,
            modifier,
        }
    }

    pub(crate) fn lang_country_modifier(&self) -> Option<String> {
        Some(format!(
            "{}_{}@{}",
            self.lang,
            self.country.clone()?,
            self.modifier.clone()?
        ))
    }

    pub(crate) fn lang_country(&self) -> Option<String> {
        Some(format!("{}_{}", self.lang, self.country.clone()?,))
    }

    pub(crate) fn lang_modifier(&self) -> Option<String> {
        Some(format!("{}@{}", self.lang, self.modifier.clone()?))
    }

    pub(crate) fn lang_only(&self) -> String {
        self.lang.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lang_country_encoding() {
        let locale = SystemLocale::new("en_US.UTF-8");
        assert_eq!(locale.lang, "en");
        assert_eq!(locale.country.unwrap(), "US");
        assert!(locale.modifier.is_none());
    }

    #[test]
    fn test_lang_country_modifier() {
        let locale = SystemLocale::new("en_US@Idk");
        assert_eq!(locale.lang, "en");
        assert_eq!(locale.country.unwrap(), "US");
        assert_eq!(locale.modifier.unwrap(), "Idk");
    }

    #[test]
    fn test_lang_country() {
        let locale = SystemLocale::new("en_US");
        assert_eq!(locale.lang, "en");
        assert_eq!(locale.country.unwrap(), "US");
    }

    #[test]
    fn test_lang_modifier() {
        let locale = SystemLocale::new("en@Idk");
        assert_eq!(locale.lang, "en");
        assert!(locale.country.is_none());
        assert_eq!(locale.modifier.unwrap(), "Idk");
    }

    #[test]
    fn test_lang_only() {
        let locale = SystemLocale::new("en");
        assert_eq!(locale.lang, "en");
        assert!(locale.country.is_none());
        assert!(locale.modifier.is_none());
    }

    #[test]
    fn test_full() {
        let locale = SystemLocale::new("en_US.UTF-8@Idk");
        assert_eq!(locale.lang, "en");
        assert_eq!(locale.country.unwrap(), "US");
        assert_eq!(locale.modifier.unwrap(), "Idk");
    }
}
