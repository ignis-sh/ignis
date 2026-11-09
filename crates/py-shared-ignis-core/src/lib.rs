//! Python wrappers around `ignis-core` primitives, shared by the `py-*` binding crates.
//!
//! [`PyProperty`] and [`PyEvent`] are type-erased: they are not generic, so they can be
//! `#[pyclass]`es, and the value type is converted to Python through [`ToPy`].
use std::path::PathBuf;
use std::sync::Mutex;

use ignis_core::event::{ConnectionHandle, Event};
use ignis_core::property::Property;
use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::{IntoPyObjectExt, PyResult};

pub use pyo3;

/// Converts a Rust value to a Python object.
///
/// `M` is a marker type owned by the binding crate. It allows the binding crate to implement
/// `ToPy<Marker>` for types from other crates (e.g. `mpris::LoopStatus`) without violating
/// the orphan rule.
pub trait ToPy<M> {
    fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>>;
}

macro_rules! impl_to_py_clone {
    ($($ty:ty),* $(,)?) => {
        $(
            impl<M> ToPy<M> for $ty {
                fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
                    self.clone().into_py_any(py)
                }
            }
        )*
    };
}

impl_to_py_clone!(
    bool, i8, i16, i32, i64, u8, u16, u32, u64, f32, f64, String, PathBuf
);

impl<M> ToPy<M> for () {
    fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        Ok(py.None())
    }
}

impl<M, T: ToPy<M>> ToPy<M> for Vec<T> {
    fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let items = self
            .iter()
            .map(|v| v.to_py(py))
            .collect::<PyResult<Vec<_>>>()?;
        PyList::new(py, items)?.into_py_any(py)
    }
}

impl<M, T: ToPy<M>> ToPy<M> for Option<T> {
    fn to_py(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        match self {
            Some(v) => v.to_py(py),
            None => Ok(py.None()),
        }
    }
}

type ConnectFn = dyn Fn(Py<PyAny>) -> ConnectionHandle + Send + Sync;
type DisconnectFn = dyn Fn(ConnectionHandle) + Send + Sync;
type ReadFn = dyn Fn(Python<'_>) -> PyResult<Py<PyAny>> + Send + Sync;

/// A handle returned by [`Event.connect`][], used to disconnect the callback.
#[pyclass(name = "ConnectionHandle")]
pub struct PyConnectionHandle {
    inner: Mutex<Option<ConnectionHandle>>,
}

/// An event which invokes connected callbacks when it is emitted.
#[pyclass(name = "Event")]
pub struct PyEvent {
    connect: Box<ConnectFn>,
    disconnect: Box<DisconnectFn>,
}

impl PyEvent {
    pub fn new<M, T>(event: Event<T>) -> Self
    where
        M: 'static,
        T: ToPy<M> + 'static,
        Event<T>: Send + Sync,
    {
        let disconnect_event = event.clone();

        Self {
            connect: Box::new(move |callback| {
                event.connect(move |value: &T| {
                    Python::attach(|py| {
                        let result = value
                            .to_py(py)
                            .and_then(|value| callback.call1(py, (value,)));

                        if let Err(e) = result {
                            e.print(py)
                        }
                    })
                })
            }),
            disconnect: Box::new(move |handle| disconnect_event.disconnect(handle)),
        }
    }
}

#[pymethods]
impl PyEvent {
    /// Registers a callback to invoke when the event is emitted.
    ///
    /// The callback receives the emitted value as its only argument.
    fn connect(&self, callback: Py<PyAny>) -> PyConnectionHandle {
        PyConnectionHandle {
            inner: Mutex::new(Some((self.connect)(callback))),
        }
    }

    /// Unregisters a callback. Disconnecting the same handle twice does nothing.
    fn disconnect(&self, handle: PyRef<'_, PyConnectionHandle>) {
        if let Some(handle) = handle.inner.lock().unwrap().take() {
            (self.disconnect)(handle)
        }
    }
}

/// A value which can change over time.
///
/// Read the current value with [`value`][] and observe changes with [`changed`][].
#[pyclass(name = "Property")]
pub struct PyProperty {
    read: Box<ReadFn>,
    changed: Py<PyEvent>,
}

impl PyProperty {
    pub fn new<M, T, A>(py: Python<'_>, property: Property<T, A>) -> PyResult<Self>
    where
        M: 'static,
        T: ToPy<M> + 'static,
        Property<T, A>: Send + Sync + 'static,
        Event<T>: Send + Sync,
    {
        let changed = Py::new(py, PyEvent::new::<M, T>(property.changed.clone()))?;

        Ok(Self {
            read: Box::new(move |py| property.read(|v| v.to_py(py))),
            changed,
        })
    }
}

#[pymethods]
impl PyProperty {
    /// The current value.
    #[getter]
    fn value(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        (self.read)(py)
    }

    /// Emitted with the new value when the property changes.
    #[getter]
    fn changed(&self, py: Python<'_>) -> Py<PyEvent> {
        self.changed.clone_ref(py)
    }
}

/// Generates a `#[getter]` returning a [`PyProperty`] for each listed field.
///
/// Meant to be invoked through a property list exported by `#[derive(ignis_core::Properties)]`:
///
/// ```ignore
/// mpris::player_properties!(py_shared_ignis_core::py_properties, Player, inner.properties, Marker);
/// ```
///
/// which expands to
///
/// ```ignore
/// py_shared_ignis_core::py_properties! { Player, inner.properties, Marker ; can_quit, ... }
/// ```
///
/// The trailing marker argument (see [`ToPy`]) is optional and defaults to `()`.
///
/// The crate invoking it must enable the `multiple-pymethods` feature of pyo3.
#[macro_export]
macro_rules! py_properties {
    ($ty:ty, $($path:ident).+, $marker:ty ; $($field:ident),* $(,)?) => {
        $crate::py_properties!(@acc [] $ty, [$($path).+], $marker ; $($field),*);
    };

    // The marker is optional; it is only needed when converting types from other crates.
    ($ty:ty, $($path:ident).+ ; $($field:ident),* $(,)?) => {
        $crate::py_properties!(@acc [] $ty, [$($path).+], () ; $($field),*);
    };

    // Accumulate one getter per field. A plain `$(...)*` over fields can't be used, because
    // `$path` is a repetition too and macro_rules would require both to repeat equally.
    (@acc [$($acc:tt)*] $ty:ty, [$($path:ident).+], $marker:ty ; $field:ident $(, $rest:ident)*) => {
        $crate::py_properties!(
            @acc
            [
                $($acc)*
                #[getter]
                fn $field(&self, py: $crate::pyo3::Python<'_>) -> $crate::pyo3::PyResult<$crate::PyProperty> {
                    $crate::PyProperty::new::<$marker, _, _>(py, self.$($path).+.$field.clone())
                }
            ]
            $ty, [$($path).+], $marker ; $($rest),*
        );
    };

    (@acc [$($acc:tt)*] $ty:ty, [$($path:ident).+], $marker:ty ;) => {
        #[$crate::pyo3::pymethods]
        impl $ty {
            $($acc)*
        }
    };
}

/// Generates a `#[getter]` returning a [`PyEvent`] for each listed field.
///
/// Meant to be invoked through an event list exported by `#[derive(ignis_core::Events)]`:
///
/// ```ignore
/// mpris::mpris_service_events!(py_shared_ignis_core::py_events, MprisService, inner.events, Marker);
/// ```
///
/// which expands to
///
/// ```ignore
/// py_shared_ignis_core::py_events! { MprisService, inner.events, Marker ; player_added, ... }
/// ```
///
/// The trailing marker argument (see [`ToPy`]) is optional and defaults to `()`.
///
/// The crate invoking it must enable the `multiple-pymethods` feature of pyo3.
#[macro_export]
macro_rules! py_events {
    ($ty:ty, $($path:ident).+, $marker:ty ; $($field:ident),* $(,)?) => {
        $crate::py_events!(@acc [] $ty, [$($path).+], $marker ; $($field),*);
    };

    // The marker is optional; it is only needed when converting types from other crates.
    ($ty:ty, $($path:ident).+ ; $($field:ident),* $(,)?) => {
        $crate::py_events!(@acc [] $ty, [$($path).+], () ; $($field),*);
    };

    // See `py_properties` for why the getters are accumulated.
    (@acc [$($acc:tt)*] $ty:ty, [$($path:ident).+], $marker:ty ; $field:ident $(, $rest:ident)*) => {
        $crate::py_events!(
            @acc
            [
                $($acc)*
                #[getter]
                fn $field(&self) -> $crate::PyEvent {
                    $crate::PyEvent::new::<$marker, _>(self.$($path).+.$field.clone())
                }
            ]
            $ty, [$($path).+], $marker ; $($rest),*
        );
    };

    (@acc [$($acc:tt)*] $ty:ty, [$($path:ident).+], $marker:ty ;) => {
        #[$crate::pyo3::pymethods]
        impl $ty {
            $($acc)*
        }
    };
}
