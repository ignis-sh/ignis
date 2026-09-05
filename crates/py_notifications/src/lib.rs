use pyo3::prelude::*;

#[pymodule]
mod ignis_notifications {
    use notifications::CloseReason as RCloseReason;
    use notifications::NotificationService as RNotificationService;
    use notifications::Urgency as RUrgency;
    use notifications::{ActionHandle, NotificationHandle};
    use pyo3::{
        exceptions::{PyIOError, PyKeyError, PyOSError, PyRuntimeError, PyValueError},
        prelude::*,
    };

    use pyo3_async_runtimes;

    fn to_py_err(e: notifications::Error) -> PyErr {
        let msg = e.to_string();
        match e {
            notifications::Error::DBusError(_) => PyOSError::new_err(msg),
            notifications::Error::NoConnection => PyOSError::new_err(msg),
            notifications::Error::IOError(_) => PyIOError::new_err(msg),
            notifications::Error::JSONError(_) => PyValueError::new_err(msg),
            notifications::Error::NotificationNotFound(_) => PyKeyError::new_err(msg),
            notifications::Error::ConnectionInitializedTwice => PyRuntimeError::new_err(msg),
        }
    }

    #[pyclass(from_py_object)]
    #[derive(Clone, Copy, PartialEq, Eq)]
    pub enum Urgency {
        Low,
        Normal,
        Critical,
    }

    #[pyclass(from_py_object)]
    #[derive(Clone, Copy, PartialEq, Eq)]
    pub enum CloseReason {
        Expired,
        Dismissed,
        DBusCall,
        Other,
    }

    impl From<&RUrgency> for Urgency {
        fn from(value: &RUrgency) -> Self {
            match value {
                RUrgency::Low => Urgency::Low,
                RUrgency::Normal => Urgency::Normal,
                RUrgency::Critical => Urgency::Critical,
            }
        }
    }

    impl From<&RCloseReason> for CloseReason {
        fn from(value: &RCloseReason) -> Self {
            match value {
                RCloseReason::Expired => Self::Expired,
                RCloseReason::Dismissed => Self::Dismissed,
                RCloseReason::DBusCall => Self::DBusCall,
                RCloseReason::Other => Self::Other,
            }
        }
    }

    #[pyclass]
    struct Action {
        inner: ActionHandle,
    }

    #[pymethods]
    impl Action {
        #[getter]
        fn notification_id(&self) -> u32 {
            self.inner.notification_id()
        }

        #[getter]
        fn label(&self) -> String {
            self.inner.label()
        }

        #[getter]
        fn action_key(&self) -> String {
            self.inner.action_key()
        }

        fn invoke<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.invoke().await.map_err(to_py_err)
            })
        }
    }

    #[pyclass]
    struct Notification {
        inner: NotificationHandle,
    }

    #[pymethods]
    impl Notification {
        #[getter]
        fn id(&self) -> u32 {
            self.inner.id()
        }

        #[getter]
        fn app_name(&self) -> String {
            self.inner.app_name()
        }

        #[getter]
        fn icon(&self) -> Option<String> {
            self.inner.icon()
        }

        #[getter]
        fn summary(&self) -> String {
            self.inner.summary()
        }

        #[getter]
        fn body(&self) -> String {
            self.inner.body()
        }

        #[getter]
        fn actions(&self) -> Vec<Action> {
            self.inner
                .actions()
                .into_iter()
                .map(|inner| Action { inner })
                .collect()
        }

        #[getter]
        fn urgency(&self) -> Urgency {
            (&self.inner.urgency()).into()
        }

        #[getter]
        fn timeout(&self) -> i32 {
            self.inner.timeout()
        }

        fn dismiss<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();
            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.dismiss().await.map_err(to_py_err)
            })
        }
    }

    #[pyclass]
    struct NotificationService {
        inner: RNotificationService,
    }

    #[pymethods]
    impl NotificationService {
        #[new]
        fn new() -> PyResult<Self> {
            Ok(Self {
                inner: RNotificationService::new(None).map_err(to_py_err)?,
            })
        }

        #[staticmethod]
        fn new_in_memory() -> Self {
            Self {
                inner: RNotificationService::new_in_memory(),
            }
        }

        fn run<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();

            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.run().await.map_err(to_py_err)
            })
        }

        fn dismiss_notification<'py>(
            &self,
            py: Python<'py>,
            id: u32,
        ) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();

            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.dismiss_notification(id).await.map_err(to_py_err)
            })
        }

        fn invoke_action<'py>(
            &self,
            py: Python<'py>,
            notification_id: u32,
            action_key: String,
        ) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();

            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner
                    .invoke_action(notification_id, &action_key)
                    .await
                    .map_err(to_py_err)
            })
        }

        #[getter]
        fn notifications(&self) -> Vec<Notification> {
            self.inner
                .get_notifications()
                .into_iter()
                .map(|inner| Notification { inner })
                .collect()
        }

        fn get_notification_by_id(&self, id: u32) -> Option<Notification> {
            Some(Notification {
                inner: self.inner.get_notification_by_id(id)?,
            })
        }

        fn clear_notifications<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
            let inner = self.inner.clone();

            pyo3_async_runtimes::tokio::future_into_py(py, async move {
                inner.clear_notifications().await.map_err(to_py_err)
            })
        }

        fn on_notified(&self, callback: Py<PyAny>) {
            self.inner
                .on_notified
                .connect(move |(id, handle, replace)| {
                    Python::attach(|py| {
                        if let Err(e) = callback.call1(
                            py,
                            (
                                id,
                                Notification {
                                    inner: handle.clone(),
                                },
                                replace,
                            ),
                        ) {
                            e.print(py)
                        }
                    });
                });
        }

        fn on_notification_closed(&self, callback: Py<PyAny>) {
            self.inner
                .on_notification_closed
                .connect(move |(id, reason)| {
                    Python::attach(|py| {
                        if let Err(e) = callback.call1(py, (id, CloseReason::from(reason))) {
                            e.print(py)
                        }
                    })
                });
        }
    }
}
