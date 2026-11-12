use crate::event::{Event, EventOwner};
use std::marker::PhantomData;
use std::sync::{Arc, RwLock};

#[derive(Default)]
struct PropertyState<T> {
    value: T,
}

pub struct Property<T, A = ReadOnly> {
    state: Arc<RwLock<PropertyState<T>>>,
    _access: PhantomData<A>,
    pub changed: Event<T>,
}

impl<T, A> Clone for Property<T, A> {
    fn clone(&self) -> Self {
        Self {
            state: self.state.clone(),
            _access: PhantomData,
            changed: self.changed.clone(),
        }
    }
}

#[derive(Default)]
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

    pub fn return_property(&self) -> Property<T, A> {
        Property {
            state: self.state.clone(),
            changed: self.changed.return_event(),
            _access: PhantomData,
        }
    }
}

impl<T: Clone, A> PropertyOwner<T, A> {
    pub fn set(&self, value: T) {
        self.state.write().unwrap().value = value.clone();
        self.changed.emit(&value);
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

#[derive(Clone)]
pub struct ReadOnly;

#[derive(Clone)]
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
        let property_clone = property.clone();

        property.changed.connect(move |value: &bool| {
            assert_eq!(property_clone.read(|v| *v), *value);
            *received_clone.lock().unwrap() = *value;
        });

        owner.set(true);

        assert!(*received.lock().unwrap());
    }
}
