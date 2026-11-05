use proc_macro::TokenStream;
use quote::quote;
use syn::{Data, DeriveInput, Fields, Ident, PathArguments, Type, parse_macro_input};

/// Generates a handle struct and an exported property list for a struct of `PropertyOwner`s.
///
/// ```ignore
/// #[derive(Properties)]
/// #[properties(handle = PlayerHandleProperties, export = player_properties)]
/// struct PlayerOwnerProperties {
///     volume: PropertyOwner<f64>,
/// }
/// ```
///
/// Generates:
/// - `pub struct PlayerHandleProperties { pub volume: Property<f64> }`
/// - `PlayerOwnerProperties::handle(&self) -> PlayerHandleProperties`
/// - `#[macro_export] macro_rules! player_properties`, which calls the passed macro with the
///   property names: `player_properties!(some::macro, args...)` expands to
///   `some::macro! { args... ; volume }`.
#[proc_macro_derive(Properties, attributes(properties))]
pub fn derive_properties(input: TokenStream) -> TokenStream {
    let kind = Kind {
        attr: "properties",
        derive: "Properties",
        owner_ty: "PropertyOwner",
        handle_ty: quote! { ::ignis_core::property::Property },
        return_fn: quote! { return_property },
    };

    let input = parse_macro_input!(input as DeriveInput);

    match expand(input, &kind) {
        Ok(tokens) => tokens.into(),
        Err(e) => e.to_compile_error().into(),
    }
}

/// Generates a handle struct and an exported event list for a struct of `EventOwner`s.
///
/// ```ignore
/// #[derive(Events)]
/// #[events(handle = MprisServiceEvents, export = mpris_service_events)]
/// struct MprisServiceOwnerEvents {
///     player_added: EventOwner<PlayerHandle>,
/// }
/// ```
///
/// Generates:
/// - `pub struct MprisServiceEvents { pub player_added: Event<PlayerHandle> }`
/// - `MprisServiceOwnerEvents::handle(&self) -> MprisServiceEvents`
/// - `#[macro_export] macro_rules! mpris_service_events`, which calls the passed macro with the
///   event names: `mpris_service_events!(some::macro, args...)` expands to
///   `some::macro! { args... ; player_added }`.
#[proc_macro_derive(Events, attributes(events))]
pub fn derive_events(input: TokenStream) -> TokenStream {
    let kind = Kind {
        attr: "events",
        derive: "Events",
        owner_ty: "EventOwner",
        handle_ty: quote! { ::ignis_core::event::Event },
        return_fn: quote! { return_event },
    };

    let input = parse_macro_input!(input as DeriveInput);

    match expand(input, &kind) {
        Ok(tokens) => tokens.into(),
        Err(e) => e.to_compile_error().into(),
    }
}

/// Describes what a derive macro operates on.
struct Kind {
    /// Name of the helper attribute, e.g. `properties`.
    attr: &'static str,
    /// Name of the derive macro, used in error messages.
    derive: &'static str,
    /// Type of the owner struct's fields, e.g. `PropertyOwner`.
    owner_ty: &'static str,
    /// Type of the handle struct's fields, e.g. `::ignis_core::property::Property`.
    handle_ty: proc_macro2::TokenStream,
    /// Method of `owner_ty` which returns `handle_ty`.
    return_fn: proc_macro2::TokenStream,
}

fn expand(input: DeriveInput, kind: &Kind) -> syn::Result<proc_macro2::TokenStream> {
    let owner = &input.ident;
    let attr_name = kind.attr;
    let derive = kind.derive;

    let mut handle: Option<Ident> = None;
    let mut export: Option<Ident> = None;

    for attr in input.attrs.iter().filter(|a| a.path().is_ident(attr_name)) {
        attr.parse_nested_meta(|meta| {
            if meta.path.is_ident("handle") {
                handle = Some(meta.value()?.parse()?);
                Ok(())
            } else if meta.path.is_ident("export") {
                export = Some(meta.value()?.parse()?);
                Ok(())
            } else {
                Err(meta.error("expected `handle` or `export`"))
            }
        })?;
    }

    let handle = handle.ok_or_else(|| {
        syn::Error::new_spanned(
            owner,
            format!("missing #[{attr_name}(handle = ...)] attribute"),
        )
    })?;

    let fields = match &input.data {
        Data::Struct(data) => match &data.fields {
            Fields::Named(fields) => &fields.named,
            _ => {
                return Err(syn::Error::new_spanned(
                    owner,
                    format!("{derive} can only be derived for structs with named fields"),
                ));
            }
        },
        _ => {
            return Err(syn::Error::new_spanned(
                owner,
                format!("{derive} can only be derived for structs"),
            ));
        }
    };

    let handle_ty = &kind.handle_ty;
    let return_fn = &kind.return_fn;

    let mut handle_fields = Vec::new();
    let mut handle_inits = Vec::new();
    let mut names = Vec::new();

    for field in fields {
        let name = field.ident.as_ref().unwrap();
        let args = generic_args(&field.ty, kind.owner_ty)?;
        let docs = field.attrs.iter().filter(|a| a.path().is_ident("doc"));

        handle_fields.push(quote! {
            #(#docs)*
            pub #name: #handle_ty #args
        });
        handle_inits.push(quote! { #name: self.#name.#return_fn() });
        names.push(name);
    }

    let export_macro = export.map(|export| {
        quote! {
            #[macro_export]
            macro_rules! #export {
                ($($cb:ident)::+ , $($args:tt)*) => {
                    $($cb)::+ ! { $($args)* ; #(#names),* }
                };
            }
        }
    });

    Ok(quote! {
        #[derive(Clone)]
        pub struct #handle {
            #(#handle_fields,)*
        }

        impl #owner {
            pub fn handle(&self) -> #handle {
                #handle {
                    #(#handle_inits,)*
                }
            }
        }

        #export_macro
    })
}

/// Returns the generic arguments of `ty` if its name is `expected`, e.g. `<T, A>` of
/// `PropertyOwner<T, A>`.
fn generic_args<'a>(ty: &'a Type, expected: &str) -> syn::Result<&'a PathArguments> {
    if let Type::Path(path) = ty
        && let Some(segment) = path.path.segments.last()
        && segment.ident == expected
    {
        return Ok(&segment.arguments);
    }

    Err(syn::Error::new_spanned(
        ty,
        format!("every field must be a `{expected}<T>`"),
    ))
}
