use std::sync::OnceLock;
use tokio::runtime::Runtime;

pub fn runtime() -> &'static Runtime {
    static RUNTIME: OnceLock<Runtime> = OnceLock::new();
    RUNTIME.get_or_init(|| Runtime::new().expect("Setting up tokio runtime needs to succeed."))
}

#[macro_export]
macro_rules! glib_async_method {
    ($this_type:ty,
    $wrapper_type:ty,
    $async_method_name:ident,
    $finish_method_name:ident,
    $imp_method:ident
    $(
        ,
        $arg_name:ident : $arg_ty:ty => $convert:expr
    )*
    $(,)?
) => {
        #[unsafe(no_mangle)]
        pub unsafe extern "C" fn $async_method_name(
            this: *mut $this_type,
            $(
                $arg_name: $arg_ty,
            )*
            cancellable: *mut gio::ffi::GCancellable,
            callback: gio::ffi::GAsyncReadyCallback,
            user_data: *mut c_void,
        ) {
            let imp = unsafe { (*this).imp() };
            let obj = unsafe { &<$wrapper_type>::from_glib_none(this) };

            let cancellable = unsafe { gio::Cancellable::from_glib_none(cancellable) };

            let closure = move |task: gio::LocalTask<bool>, _: Option<&$wrapper_type>| {
                let result: *mut gio::ffi::GAsyncResult =
                    task.upcast_ref::<gio::AsyncResult>().to_glib_none().0;

                if let Some(func) = callback {
                    unsafe { func(this as *mut _, result, user_data) }
                }
            };

            let task = unsafe { gio::LocalTask::new(Some(obj), Some(&cancellable), closure) };

            glib::MainContext::ref_thread_default().spawn_local(async move {
                let _guard = runtime().enter();

                $(
                    let $arg_name = $convert;
                )*

                let res = imp.
                        $imp_method(
                            $(
                                $arg_name,
                            )*
                        )
                        .await
                        .map(|_| true);

                task.return_result(res);
            });
        }

        #[unsafe(no_mangle)]
        pub unsafe extern "C" fn $finish_method_name(
            _this: *mut $this_type,
            res: *mut gio::ffi::GAsyncResult,
            error: *mut *mut glib::ffi::GError,
        ) -> bool {
            let task = unsafe { gio::Task::<bool>::from_glib_none(res as *mut gio::ffi::GTask) };

            return match unsafe { task.propagate() } {
                Ok(_) => true,
                Err(e) => {
                    if !error.is_null() {
                        unsafe { *error = e.into_glib_ptr() };
                    }
                    false
                }
            };
        }
    };
}
