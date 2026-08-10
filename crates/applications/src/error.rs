use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("Notify error: {0}")]
    NotifyError(#[from] notify::Error),

    #[error("Exec string is empty")]
    ExecEmpty,

    #[error("I/O Error: {0}")]
    IOError(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, Error>;
