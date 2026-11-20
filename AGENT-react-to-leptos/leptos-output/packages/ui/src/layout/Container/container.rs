use leptos::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ContainerMaxWidth {
    Narrow,
    #[default]
    Default,
    Wide,
    Full,
    Page,
}

impl ContainerMaxWidth {
    pub fn class(&self) -> &'static str {
        match self {
            Self::Narrow => "max-w-narrow",
            Self::Default => "max-w-page",
            Self::Wide => "max-w-xl",
            Self::Full => "max-w-none",
            Self::Page => "max-w-page",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ContainerHorizontalPadding {
    None,
    Sm,
    #[default]
    Default,
    Lg,
}

impl ContainerHorizontalPadding {
    pub fn class(&self) -> &'static str {
        match self {
            Self::None => "px-0",
            Self::Sm => "px-4 md:px-6",
            Self::Default => "px-4 md:px-8",
            Self::Lg => "px-6 md:px-12",
        }
    }
}

#[component]
pub fn Container(
    #[prop(default = ContainerMaxWidth::Default)] max_width: ContainerMaxWidth,
    #[prop(default = ContainerHorizontalPadding::Default)] horizontal_padding: ContainerHorizontalPadding,
    #[prop(optional, into)] class: String,
    #[prop(optional)] id: Option<String>,
    #[prop(optional)] style: Option<String>,
    #[prop(optional)] aria_label: Option<String>,
    #[prop(optional)] children: Option<Children>,
) -> impl IntoView {
    let classes = format!(
        "w-full mx-auto {} {} {}",
        max_width.class(),
        horizontal_padding.class(),
        class
    );

    view! {
        <div class=classes id=id style=style aria-label=aria_label>
            {children.map(|c| c())}
        </div>
    }
}