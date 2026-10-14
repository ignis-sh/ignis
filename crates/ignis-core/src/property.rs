use std::marker::PhantomData;
use std::sync::{Arc, RwLock};

struct PropertyState<T> {
    value: T,
}

pub struct Property<T, A = ReadOnly> {
    state: Arc<RwLock<PropertyState<T>>>,
    _access: PhantomData<A>,
}

pub struct PropertyOwner<T, A = ReadOnly> {
    state: Arc<RwLock<PropertyState<T>>>,
    _access: PhantomData<A>,
}

impl<T, A> PropertyOwner<T, A> {
    pub fn new(default_value: T) -> Self {
        let state = Arc::new(RwLock::new(PropertyState {
            value: default_value,
        }));

        Self {
            state: Arc::clone(&state),
            _access: PhantomData,
        }
    }

    pub fn set(&self, value: T) {
        let mut state = self.state.write().unwrap();
        state.value = value;
    }

    pub fn return_property(&self) -> Property<T, A> {
        Property {
            state: self.state.clone(),
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
