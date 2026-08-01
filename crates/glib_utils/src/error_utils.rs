pub trait IntoGLibError<T> {
    type Error;

    fn into_glib_error<D>(self) -> Result<T, glib::Error>
    where
        D: glib::error::ErrorDomain + for<'a> From<&'a Self::Error>;
}

impl<T, E> IntoGLibError<T> for Result<T, E>
where
    E: std::error::Error,
{
    type Error = E;

    fn into_glib_error<D>(self) -> Result<T, glib::Error>
    where
        D: glib::error::ErrorDomain + for<'a> From<&'a E>,
    {
        self.map_err(|e| glib::Error::new(<D as From<_>>::from(&e), &e.to_string()))
    }
}
