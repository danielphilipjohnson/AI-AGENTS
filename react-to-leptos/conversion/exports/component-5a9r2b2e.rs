use leptos::prelude::*;
use tailwind_fuse::tw_merge;

/// Breakpoint values used for responsive column classes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Breakpoint {
    #[default]
    Md,
    Sm,
    Lg,
}

impl Breakpoint {
    /// Returns the breakpoint prefix string (`sm`, `md`, or `lg`).
    fn prefix(self) -> &'static str {
        match self {
            Breakpoint::Sm => "sm",
            Breakpoint::Md => "md",
            Breakpoint::Lg => "lg",
        }
    }

    /// Returns the responsive grid‑cols class for the given breakpoint and column count.
    fn responsive_cols(self, cols: u32) -> String {
        format!("{}:grid-cols-{}", self.prefix(), cols)
    }
}

/// Returns the Tailwind class for a given column span.
/// Defaults to `col-span-1` if the span is out of range.
fn col_span_class(span: u32) -> &'static str {
    match span {
        1 => "col-span-1",
        2 => "col-span-2",
        3 => "col-span-3",
        4 => "col-span-4",
        5 => "col-span-5",
        6 => "col-span-6",
        7 => "col-span-7",
        8 => "col-span-8",
        9 => "col-span-9",
        10 => "col-span-10",
        11 => "col-span-11",
        12 => "col-span-12",
        _ => "col-span-1",
    }
}

#[component]
pub fn Grid(
    #[prop(optional, default = 2)] cols: u32,
    #[prop(optional, default = 6)] row_gap: u32,
    #[prop(optional, default = 6)] col_gap: u32,
    #[prop(optional, default = Breakpoint::Md)] breakpoint: Breakpoint,
    #[prop(optional, into)] class: String,
    children: Children,
) -> impl IntoView {
    let classes = tw_merge!(
        "grid",
        "grid-cols-1",
        breakpoint.responsive_cols(cols),
        format!("gap-y-{}", row_gap),
        format!("gap-x-{}", col_gap),
        class
    );
    view! {
        <div class=classes>
            {children()}
        </div>
    }
}

#[component]
pub fn GridCol(
    #[prop(optional, default = 1)] span: u32,
    #[prop(optional, into)] class: String,
    children: Children,
) -> impl IntoView {
    let span_class = col_span_class(span);
    let classes = tw_merge!(span_class, class);
    view! {
        <div class=classes>
            {children()}
        </div>
    }
}
