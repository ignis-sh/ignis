use gio::prelude::*;
use glib::object::IsA;

pub fn search_in_list_store<T, F>(store: &gio::ListStore, predicate: F) -> Option<u32>
where
    T: IsA<glib::Object>,
    F: Fn(&T) -> bool,
{
    for i in 0..store.n_items() {
        let Ok(element) = store.item(i)?.downcast::<T>() else {
            continue;
        };

        if predicate(&element) {
            return Some(i);
        }
    }

    None
}
