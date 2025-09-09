import os
import ignis
import shutil
from loguru import logger


_OLD_CACHE_WALLPAPER_PATH = f"{ignis.CACHE_DIR}/wallpaper"
CACHE_WALLPAPER_PATH = f"{ignis.DATA_DIR}/wallpaper"

# FIXME: remove after v0.6 release
if not os.path.exists(CACHE_WALLPAPER_PATH) and os.path.exists(
    _OLD_CACHE_WALLPAPER_PATH
):
    logger.warning(
        f"Copying the cached wallpaper to the new directory: {_OLD_CACHE_WALLPAPER_PATH} -> {CACHE_WALLPAPER_PATH}"
    )
    shutil.copy(_OLD_CACHE_WALLPAPER_PATH, CACHE_WALLPAPER_PATH)
