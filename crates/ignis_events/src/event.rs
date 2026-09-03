use std::collections::HashMap;
use std::sync::Arc;
use std::sync::Mutex;

type Callback<T> = dyn Fn(&T) + Send + Sync + 'static;

#[derive(Default)]
struct EventInner<T> {
    callbacks: Mutex<HashMap<usize, Arc<Callback<T>>>>,
    next_id: Mutex<usize>,
}

/// A struct which represents some event.
///
/// Generic parameter `T` is a type of argument which callbacks accept.
#[derive(Clone, Default)]
pub struct Event<T> {
    inner: Arc<EventInner<T>>,
}

impl<T> Event<T> {
    /// Creates a new instance of an event.
    pub fn new() -> Self {
        Self {
            inner: Arc::new(EventInner {
                callbacks: Mutex::new(HashMap::new()),
                next_id: Mutex::new(0),
            }),
        }
    }

    /// Registers the provided callback to invoke when the event is emitted.
    ///
    /// Returns an ID which can be used to unregister the callback using
    /// [`disconnect`][Self::disconnect].
    pub fn connect<F>(&self, callback: F) -> usize
    where
        F: Fn(&T) + Send + Sync + 'static,
    {
        let callback_id = {
            let mut next_id = self.inner.next_id.lock().unwrap();
            let id = *next_id;
            *next_id += 1;
            id
        };

        self.inner
            .callbacks
            .lock()
            .unwrap()
            .insert(callback_id, Arc::new(callback));

        callback_id
    }

    /// Emits the event.
    ///
    /// It calls all callbacks with `&T` as the argument.
    pub fn emit(&self, value: &T) {
        let callbacks = {
            let map = self.inner.callbacks.lock().unwrap();
            map.values().cloned().collect::<Vec<_>>()
        };

        for callback in callbacks {
            callback(value)
        }
    }

    /// Unregister the callback by its ID.
    pub fn disconnect(&self, handle: usize) {
        self.inner.callbacks.lock().unwrap().remove(&handle);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_emit() {
        let event = Event::new();
        let received = Arc::new(Mutex::new(None));

        let received_clone = Arc::clone(&received);

        event.connect(move |value: &i32| {
            *received_clone.lock().unwrap() = Some(*value);
        });

        event.emit(&67);

        assert_eq!(*received.lock().unwrap(), Some(67));
    }
}
