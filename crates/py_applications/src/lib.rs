use pyo3::prelude::*;

/// Access desktop application entries defined according to the [XDG Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry/latest).
///
/// ### Example
///
/// ```python
/// from ignis_applications import ApplicationService
///
/// service = ApplicationService()
///
/// # display names of all applications
/// for i in service.apps:
///     print(i.name)
///
/// # Fuzzy search by name
/// firefox = service.search_by_name("firfx")
///
/// # Launch application
/// firefox.launch()
///
/// # See actions
///
/// for action in firefox.actions:
///     print(action.name)
///
///     # Launch action
///     # action.launch()
/// ```
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

    /// A desktop application action.
    #[pyclass]
    struct Action {
        inner: ActionHandle,
    }

    #[pymethods]
    impl Action {
        /// Launches the action.
        fn launch(&self) -> PyResult<()> {
            self.inner.launch().map_err(to_py_err)
        }

        /// The name of the action.
        ///
        /// For example: `Launch in new window`.
        #[getter]
        fn name(&self) -> String {
            self.inner.name()
        }

        /// The localized name of the action.
        #[getter]
        fn name_locale(&self) -> String {
            self.inner.name_locale()
        }

        /// The icon of the action.
        #[getter]
        fn icon(&self) -> Option<String> {
            self.inner.icon()
        }

        /// The localized icon of the action.
        #[getter]
        fn icon_locale(&self) -> Option<String> {
            self.inner.icon_locale()
        }

        /// The exec string of the action.
        #[getter]
        fn exec(&self) -> Option<String> {
            self.inner.exec()
        }
    }

    /// A desktop application.
    #[pyclass]
    struct DesktopApp {
        inner: DesktopAppHandle,
    }

    #[pymethods]
    impl DesktopApp {
        /// Launches the application based on the [`exec`][exec] string.
        ///
        /// Starts a default terminal window if [`terminal`][terminal] is `true`.
        ///
        /// The launched child process is detached from this process.
        fn launch(&self) -> PyResult<()> {
            self.inner.launch().map_err(to_py_err)
        }

        /// The unique ID of the application.
        #[getter]
        pub fn app_id(&self) -> String {
            self.inner.app_id()
        }

        /// The name of the application.
        ///
        /// For example: `firefox`.
        #[getter]
        fn name(&self) -> String {
            self.inner.name()
        }

        /// The localized name of the application.
        #[getter]
        pub fn name_locale(&self) -> String {
            self.inner.name_locale()
        }

        /// The generic name of the application.
        ///
        /// For example: `Web browser`.
        #[getter]
        pub fn generic_name(&self) -> Option<String> {
            self.inner.generic_name()
        }

        /// The localized generic name of the application.
        #[getter]
        pub fn generic_name_locale(&self) -> Option<String> {
            self.inner.generic_name_locale()
        }

        /// The icon of the application.
        ///
        /// It's either the name of the icon or the absolute path.
        #[getter]
        pub fn icon(&self) -> Option<String> {
            self.inner.icon()
        }

        /// The localized icon of the application.
        #[getter]
        pub fn icon_locale(&self) -> Option<String> {
            self.inner.icon_locale()
        }

        /// A list of keywords describing the application.
        #[getter]
        pub fn keywords(&self) -> Vec<String> {
            self.inner.keywords()
        }

        /// A list of localized keywords describing the application.
        #[getter]
        pub fn keywords_locale(&self) -> Vec<String> {
            self.inner.keywords_locale()
        }

        /// The string containing the program to execute, possibly with arguments.
        #[getter]
        pub fn exec(&self) -> Option<String> {
            self.inner.exec()
        }

        /// Whether the program should run in a terminal window.
        #[getter]
        pub fn terminal(&self) -> bool {
            self.inner.terminal()
        }

        /// A list of application actions. Can be empty.
        #[getter]
        pub fn actions(&self) -> Vec<Action> {
            self.inner
                .actions()
                .into_iter()
                .map(|handle| Action { inner: handle })
                .collect()
        }
    }

    /// A service to access desktop applications.
    /// It loads all application entries from `XDG_DATA_DIRS` and gets the system locale.
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

        /// Starts watching for changes in application entries. Re-initializes apps if a change occurs.
        fn watch(&self) -> PyResult<()> {
            self.inner.watch().map_err(to_py_err)?;
            Ok(())
        }

        /// A list of applications.
        #[getter]
        fn apps(&self) -> Vec<DesktopApp> {
            self.inner
                .apps()
                .into_iter()
                .map(|handle| DesktopApp { inner: handle })
                .collect()
        }

        /// An application by its ID, or `None` if it is not found.
        fn get_app_by_id(&self, app_id: &str) -> Option<DesktopApp> {
            Some(DesktopApp {
                inner: self.inner.app_by_id(app_id)?,
            })
        }

        /// Fuzzily search through the application entries by provided application name.
        fn search_by_name(&self, query: &str) -> Vec<DesktopApp> {
            self.inner
                .search_by_name(query)
                .into_iter()
                .map(|handle| DesktopApp { inner: handle })
                .collect()
        }

        /// Invoke a callback when application list changes.
        ///
        /// ## Example
        ///
        /// ```python
        /// from ignis_applications import ApplicationService
        ///
        /// service = ApplicationService()
        /// service.watch()
        ///
        /// # You can try to install/remove some program on your system
        /// # and "refreshed" will be printed
        /// service.on_apps_refreshed(lambda: print("refreshed!"))
        /// ```
        fn on_apps_refreshed(&self, callback: Py<PyAny>) {
            self.inner.on_apps_refreshed.connect(move |_| {
                Python::attach(|py| {
                    if let Err(e) = callback.call0(py) {
                        e.print(py)
                    }
                });
            });
        }
    }
}
