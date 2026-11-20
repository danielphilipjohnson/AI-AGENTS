use leptos::prelude::*;
use tailwind_fuse::tw_merge;

pub enum Breakpoint {
    Sm,
    Md,
    Lg,
}

#[derive(Props)]
pub struct GridColProps {
    #[prop(optional)]
    cols: Option<u32>,
    #[prop(optional)]
    class: Option<String>,
    children: Children,
}

#[derive(Props)]
pub struct GridProps {
    #[prop(optional)]
    cols: Option<u32>,
    #[prop(optional)]
    row_gap: Option<u32>,
    #[prop(optional)]
    col_gap: Option<u32>,
    #[prop(optional)]
    breakpoint: Option<Breakpoint>,
    #[prop(optional)]
    class: Option<String>,
    #[prop(optional)]
    children: Option<Children>,
}

fn responsive_cols(bp: Breakpoint, cols: u32) -> String {
    match bp {
        Breakpoint::Sm => format!("sm:grid-cols-{}", cols),
        Breakpoint::Md => format!("md:grid-cols-{}", cols),
        Breakpoint::Lg => format!("lg:grid-cols-{}", cols),
    }
}

fn col_span_class(cols: u32) -> &'static str {
    match cols {
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
        _ => unreachable!(),
    }
}

#[component]
pub fn Grid(props: GridProps) -> impl IntoView {
    let classes = tw_merge!(
        "grid",
        "grid-cols-1",
        responsive_cols(props.breakpoint.unwrap_or(Breakpoint::Md), props.cols.unwrap_or(2)),
        match props.row_gap {
            Some(row_gap) => format!("gap-y-{}", row_gap),
            None => "gap-y-6".to_string(),
        },
        match props.col_gap {
            Some(col_gap) => format!("gap-x-{}", col_gap),
            None => "gap-x-6".to_string(),
        },
        props.class.clone().unwrap_or_default(),
    );

    view! {
        <div class=classes>
            {props.children.map(|c| c())}
        </div>
    }
}

#[component]
pub fn GridCol(props: GridColProps) -> impl IntoView {
    let base_class = match props.cols {
        Some(cols) => col_span_class(cols).to_string(),
        None => props.class.clone().unwrap_or_default(),
    };
    let classes = tw_merge!(base_class, props.class.clone().unwrap_or_default());

    view! {
        <div class=classes>
            {props.children()}
        </div>
    }
}