use pyo3::prelude::*;

#[pymodule]
mod ignis_applications {
    use pyo3::prelude::*;

    use applications::{
        ActionHandle, ApplicationService as RApplicationService, DesktopAppHandle, Error as RError,
    };
    use pyo3::exceptions::{PyOSError, PyValueError};

    fn to_py_err(e: RError) -> PyErr {
        let msg = e.to_string();

        match e {
            RError::NotifyError(_) => PyOSError::new_err(msg),
            RError::IOError(_) => PyOSError::new_err(msg),
            RError::ExecEmpty => PyValueError::new_err(msg),
        }
    }

    #[pyclass]
    struct Action {
        inner: ActionHandle,
    }

    #[pymethods]
    impl Action {
        fn run(&self) -> PyResult<()> {
            self.inner.run().map_err(to_py_err)
        }

        #[getter]
        fn name(&self) -> String {
            self.inner.name()
        }

        #[getter]
        fn name_locale(&self) -> String {
            self.inner.name_locale()
        }

        #[getter]
        fn icon(&self) -> Option<String> {
            self.inner.icon()
        }

        #[getter]
        fn icon_locale(&self) -> Option<String> {
            self.inner.icon_locale()
        }

        #[getter]
        fn exec(&self) -> Option<String> {
            self.inner.exec()
        }
    }

    #[pyclass]
    struct DesktopApp {
        inner: DesktopAppHandle,
    }

    #[pymethods]
    impl DesktopApp {
        fn run(&self) -> PyResult<()> {
            self.inner.run().map_err(to_py_err)
        }

        #[getter]
        pub fn app_id(&self) -> String {
            self.inner.app_id()
        }

        #[getter]
        fn name(&self) -> Option<String> {
            self.inner.name()
        }

        #[getter]
        pub fn name_locale(&self) -> Option<String> {
            self.inner.name_locale()
        }

        #[getter]
        pub fn generic_name(&self) -> Option<String> {
            self.inner.generic_name()
        }

        #[getter]
        pub fn generic_name_locale(&self) -> Option<String> {
            self.inner.generic_name_locale()
        }

        #[getter]
        pub fn icon(&self) -> Option<String> {
            self.inner.icon()
        }

        #[getter]
        pub fn icon_locale(&self) -> Option<String> {
            self.inner.icon_locale()
        }

        #[getter]
        pub fn keywords(&self) -> Vec<String> {
            self.inner.keywords()
        }

        #[getter]
        pub fn keywords_locale(&self) -> Vec<String> {
            self.inner.keywords_locale()
        }

        #[getter]
        pub fn exec(&self) -> Option<String> {
            self.inner.exec()
        }

        #[getter]
        pub fn terminal(&self) -> bool {
            self.inner.terminal()
        }

        #[getter]
        pub fn actions(&self) -> Vec<Action> {
            self.inner
                .actions()
                .into_iter()
                .map(|handle| Action { inner: handle })
                .collect()
        }
    }

    #[pyclass]
    struct ApplicationService {
        inner: RApplicationService,
    }

    #[pymethods]
    impl ApplicationService {
        #[new]
        fn new() -> Self {
            Self {
                inner: RApplicationService::new(),
            }
        }

        fn watch(&self) -> PyResult<()> {
            self.inner.watch().map_err(to_py_err)?;
            Ok(())
        }

        #[getter]
        fn apps(&self) -> Vec<DesktopApp> {
            self.inner
                .apps()
                .into_iter()
                .map(|handle| DesktopApp { inner: handle })
                .collect()
        }

        fn get_app_by_id(&self, app_id: &str) -> Option<DesktopApp> {
            Some(DesktopApp {
                inner: self.inner.app_by_id(app_id)?,
            })
        }
    }
}
