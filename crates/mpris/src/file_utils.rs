use crate::private_prelude::*;
use directories::ProjectDirs;
use std::fs;
use std::path::PathBuf;

pub(crate) fn get_service_cache_dir() -> Result<PathBuf> {
    let proj = ProjectDirs::from("ignis-mpris", "ignis", "ignis-mpris")
        .ok_or(Error::CacheDirRetrieveError)?;
    let cache_dir = proj.cache_dir();
    fs::create_dir_all(cache_dir)?;
    Ok(cache_dir.to_path_buf())
}

pub(crate) fn get_cached_art_cover_dir(cache_dir: PathBuf) -> Result<PathBuf> {
    let dir = cache_dir.join("images");
    fs::create_dir_all(&dir)?;
    Ok(dir)
}
