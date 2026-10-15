use crate::event::{Event, EventOwner};
use std::marker::PhantomData;
use std::sync::{Arc, RwLock};

struct PropertyState<T> {
    value: T,
}

pub struct Property<T, A = ReadOnly> {
    state: Arc<RwLock<PropertyState<T>>>,
    _access: PhantomData<A>,
    pub changed: Event<T>,
}

pub struct PropertyOwner<T, A = ReadOnly> {
    state: Arc<RwLock<PropertyState<T>>>,
    // changed is emitted automatically in set()
    changed: EventOwner<T>,
    _access: PhantomData<A>,
}

impl<T, A> PropertyOwner<T, A> {
    pub fn new(default_value: T) -> Self {
        let state = Arc::new(RwLock::new(PropertyState {
            value: default_value,
        }));

        Self {
            state: Arc::clone(&state),
            changed: EventOwner::new(),
            _access: PhantomData,
        }
    }

    pub fn set(&self, value: T) {
        self.changed.emit(&value);

        let mut state = self.state.write().unwrap();
        state.value = value;
    }

    pub fn return_property(&self) -> Property<T, A> {
        Property {
            state: self.state.clone(),
            changed: self.changed.return_event(),
            _access: PhantomData,
        }
    }
}

impl<T, A> Property<T, A> {
    pub fn read<R>(&self, f: impl FnOnce(&T) -> R) -> R {
        let state = self.state.read().unwrap();
        f(&state.value)
    }
}

impl<T> Property<T, ReadWrite> {
    pub fn write(&self, value: T) {
        let mut state = self.state.write().unwrap();

        state.value = value;
    }
}

pub struct ReadOnly;
pub struct ReadWrite;

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    #[test]
    fn test_changed() {
        let owner: PropertyOwner<bool> = PropertyOwner::new(false);

        let property = owner.return_property();

        let received = Arc::new(Mutex::new(false));

        let received_clone = Arc::clone(&received);

        property.changed.connect(move |value: &bool| {
            *received_clone.lock().unwrap() = *value;
        });

        owner.set(true);

        assert_eq!(*received.lock().unwrap(), true);
    }
}
