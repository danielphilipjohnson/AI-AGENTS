use leptos::prelude::*;
use tailwind_fuse::tw_merge;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
enum Breakpoint {
    Sm,
    Md,
    Lg,
}

#[component]
pub fn Grid(
    cols: u8,
    row_gap: u16,
    col_gap: u16,
    breakpoint: Option<Breakpoint>,
    class: String,
    children: Children,
) -> impl IntoView {
    let responsive_cols = move |bp: Breakpoint, cols: u8| -> String {
        format!("{bp}:grid-cols-{cols}")
    };

    let col_span_class_map: std::collections::HashMap<u8, String> = std::collections::HashMap::from([
        (1, "col-span-1".into()),
        (2, "col-span-2".into()),
        (3, "col-span-3".into()),
        (4, "col-span-4".into()),
        (5, "col-span-5".into()),
        (6, "col-span-6".into()),
        (7, "col-span-7".into()),
        (8, "col-span-8".into()),
        (9, "col-span-9".into()),
        (10, "col-span-10".into()),
        (11, "col-span-11".into()),
        (12, "col-span-12".into()),
    ]);

    let span_class = col_span_class_map.get(&cols).unwrap_or(&col_span_class_map.get(&1).unwrap());

    html! {
        <div class={tw_merge!("grid", "grid-cols-1", responsive_cols(breakpoint.unwrap_or(Breakpoint::Md), cols), format!("gap-y-{}", row_gap), format!("gap-x-{}", col_gap), class)}>
            {children}
        </div>
    }
}

#[component]
pub fn GridCol(
    span: Option<u8>,
    class: String,
    children: Children,
) -> impl IntoView {
    let span_class = match span {
        Some(span) => col_span_class_map.get(&span).unwrap_or(&col_span_class_map.get(&1).unwrap()),
        None => col_span_class_map.get(&1).unwrap(),
    };

    html! {
        <div class={tw_merge!(span_class, class)}>
            {children}
        </div>
    }
}
