from gi.repository import GdkPixbuf  # type: ignore


def crop_pixbuf(pixbuf: GdkPixbuf.Pixbuf, width: int, height: int) -> GdkPixbuf.Pixbuf:
    """
    Crop the ``GdkPixbuf.Pixbuf`` to the given width and height.

    Args:
        pixbuf: The source pixbuf.
        width: The width to crop to.
        height: The height to crop to.

    Returns:
        The cropped pixbuf.
    """
    img_width = pixbuf.get_width()
    img_height = pixbuf.get_height()

    # Calculate the aspect ratios
    target_aspect_ratio = width / height
    current_aspect_ratio = img_width / img_height

    if current_aspect_ratio > target_aspect_ratio:
        # Image is wider than aspect ratio, crop the width
        target_width = int(img_height * target_aspect_ratio)
        target_height = img_height
    else:
        # Image is taller than aspect ratio, crop the height
        target_width = img_width
        target_height = int(img_width / target_aspect_ratio)

    crop_x = (img_width - target_width) // 2
    crop_y = (img_height - target_height) // 2

    cropped_image = pixbuf.new_subpixbuf(crop_x, crop_y, target_width, target_height)
    return cropped_image


def scale_pixbuf(
    pixbuf: GdkPixbuf.Pixbuf, width: int, height: int
) -> "GdkPixbuf.Pixbuf | None":
    """
    Scale a ``GdkPixbuf.Pixbuf`` to the given width and height.

    Args:
        pixbuf: The source GdkPixbuf.Pixbuf.
        width: The target width.
        height: The target height.

    Returns:
        The scaled GdkPixbuf.Pixbuf or ``None``.
    """
    return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
