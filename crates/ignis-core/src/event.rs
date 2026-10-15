use std::collections::HashMap;
use std::sync::Arc;
use std::sync::RwLock;

type Callback<T> = dyn Fn(&T) + Send + Sync + 'static;

pub struct ConnectionHandle {
    callback_id: usize,
}

struct EventState<T> {
    callbacks: HashMap<usize, Arc<Callback<T>>>,
    next_id: usize,
}

pub struct EventOwner<T> {
    state: Arc<RwLock<EventState<T>>>,
}

/// A struct which represents some event.
///
/// Generic parameter `T` is a type of argument which callbacks accept.
pub struct Event<T> {
    state: Arc<RwLock<EventState<T>>>,
}

impl<T> EventOwner<T> {
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(EventState {
                callbacks: HashMap::new(),
                next_id: 0,
            })),
        }
    }

    /// Emits the event.
    ///
    /// It calls all callbacks with `&T` as the argument.
    pub fn emit(&self, value: &T) {
        let callbacks = self
            .state
            .read()
            .unwrap()
            .callbacks
            .values()
            .cloned()
            .collect::<Vec<_>>();

        for callback in callbacks {
            callback(value)
        }
    }

    pub fn return_event(&self) -> Event<T> {
        Event {
            state: self.state.clone(),
        }
    }
}

impl<T> Event<T> {
    /// Registers the provided callback to invoke when the event is emitted.
    ///
    /// Returns an ID which can be used to unregister the callback using
    /// [`disconnect`][Self::disconnect].
    pub fn connect<F>(&self, callback: F) -> ConnectionHandle
    where
        F: Fn(&T) + Send + Sync + 'static,
    {
        let mut guard = self.state.write().unwrap();

        let callback_id = {
            let id = guard.next_id;
            guard.next_id += 1;
            id
        };

        guard.callbacks.insert(callback_id, Arc::new(callback));

        ConnectionHandle { callback_id }
    }

    /// Unregister the callback by its ID.
    pub fn disconnect(&self, handle: ConnectionHandle) {
        self.state
            .write()
            .unwrap()
            .callbacks
            .remove(&handle.callback_id);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    #[test]
    fn test_emit() {
        let event_owner = EventOwner::new();
        let event = event_owner.return_event();
        let received = Arc::new(Mutex::new(None));

        let received_clone = Arc::clone(&received);

        event.connect(move |value: &i32| {
            *received_clone.lock().unwrap() = Some(*value);
        });

        event_owner.emit(&67);

        assert_eq!(*received.lock().unwrap(), Some(67));
    }
}
