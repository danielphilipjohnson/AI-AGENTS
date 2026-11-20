use leptos::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ContainerMaxWidth {
    #[default]
    Narrow,
    Default,
    Wide,
    Full,
    Page,
}

impl ContainerMaxWidth {
    pub fn class(&self) -> &'static str {
        match self {
            ContainerMaxWidth::Narrow => "max-w-narrow",
            ContainerMaxWidth::Default => "max-w-page",
            ContainerMaxWidth::Wide => "max-w-xl",
            ContainerMaxWidth::Full => "max-w-none",
            ContainerMaxWidth::Page => "max-w-page",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ContainerHorizontalPadding {
    #[default]
    None,
    Sm,
    Default,
    Lg,
}

impl ContainerHorizontalPadding {
    pub fn class(&self) -> &'static str {
        match self {
            ContainerHorizontalPadding::None => "px-0",
            ContainerHorizontalPadding::Sm => "px-4 md:px-6",
            ContainerHorizontalPadding::Default => "px-4 md:px-8",
            ContainerHorizontalPadding::Lg => "px-6 md:px-12",
        }
    }
}

#[component]
pub fn Container(
    cx: Scope,
    #[prop(default = ContainerMaxWidth::Default)] max_width: ContainerMaxWidth,
    #[prop(default = ContainerHorizontalPadding::Default)] horizontal_padding: ContainerHorizontalPadding,
    #[prop(optional, into)] class_name: String,
    #[prop(optional)] id: Option<String>,
    #[prop(optional)] style: Option<String>,
    #[prop(optional)] aria_label: Option<String>,
    #[prop(optional)] children: Option<Children>,
) -> impl IntoView {
    let classes = format!(
        "w-full mx-auto {} {} {}",
        max_width.class(),
        horizontal_padding.class(),
        class_name
    );
    view! { cx,
        <div
            class=classes
            id=id
            style=style
            aria-label=aria_label
        >
            {children.map(|c| c())}
        </div>
    }
}