use leptos::prelude::*;
use tailwind_fuse::tw_merge!;

pub enum Breakpoint {
    Sm,
    Md,
    Lg,
}

pub enum GridColProps {
    ColSpan(u32),
    Class(String),
    Children(Children),
}

pub enum GridProps {
    Cols(u32),
    RowGap(u32),
    ColGap(u32),
    Breakpoint(Breakpoint),
    Class(String),
    Children(Children),
}

pub fn responsive_cols(bp: Breakpoint, cols: u32) -> &'static str {
    match bp {
        Breakpoint::Sm => format!("sm:grid-cols-{}", cols).as_str(),
        Breakpoint::Md => format!("md:grid-cols-{}", cols).as_str(),
        Breakpoint::Lg => format!("lg:grid-cols-{}", cols).as_str(),
    }
}

pub fn grid_col(cx: ComponentX, span: GridColProps) -> impl IntoView {
    match span {
        GridColProps::ColSpan(span) => {
            let span_class = COL_SPAN_CLASS_MAP[span] else { COL_SPAN_CLASS_MAP[1] };
            view! {
                <div class=cx.classes(span_class.to_string())>
                    {cx.children()}
                </div>
            }
        }
        GridColProps::Class(class) => {
            view! {
                <div class=cx.classes(class)>
                    {cx.children()}
                </div>
            }
        }
        GridColProps::Children(children) => {
            view! {
                <div class=cx.classes()>
                    {children}
                </div>
            }
        }
    }
}

pub fn grid(cx: ComponentX, props: GridProps) -> impl IntoView {
    let classes = cx.classes(
        "grid",
        "grid-cols-1",
        responsive_cols(props.breakpoint, props.cols),
        format!("gap-y-{}", props.row_gap).as_str(),
        format!("gap-x-{}", props.col_gap).as_str(),
        props.class,
    );

    view! {
        <div class=classes>
            {props.children}
        </div>
    }
}

pub fn grid_props_default() -> GridProps {
     GridProps {
        cols: 2,
        row_gap: 6,
        col_gap: 6,
        breakpoint: Breakpoint::Md,
        class: String::new(),
        children: Signal::default(),
    }
}
