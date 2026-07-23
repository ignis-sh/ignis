use crate::private_prelude::*;
use std::fs;

pub(crate) fn get_service_cache_dir(xdg_cache_dir: Option<PathBuf>) -> Result<PathBuf> {
    let dir = xdg_cache_dir
        .unwrap_or_else(glib::user_cache_dir)
        .join("ignis_notifications");

    fs::create_dir_all(&dir)?;
    Ok(dir)
}

pub(crate) fn get_history_file_path(xdg_cache_dir: Option<PathBuf>) -> Result<PathBuf> {
    Ok(get_service_cache_dir(xdg_cache_dir)?.join("notifications.json"))
}

pub(crate) fn get_image_dir(xdg_cache_dir: Option<PathBuf>) -> Result<PathBuf> {
    let dir = get_service_cache_dir(xdg_cache_dir)?.join("images");
    fs::create_dir_all(&dir)?;
    Ok(dir)
}
