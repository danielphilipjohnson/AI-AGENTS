use leptos::prelude::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
enum SectionSpacing {
    None,
    Sm,
    Md,
    Lg,
    Xl,
    TwoXl,
}

impl SectionSpacing {
    fn class_name(&self) -> &'static str {
        match self {
            SectionSpacing::None => "pt-0",
            SectionSpacing::Sm => "pt-8",
            SectionSpacing::Md => "pt-12",
            SectionSpacing::Lg => "pt-16",
            SectionSpacing::Xl => "pt-24",
            SectionSpacing::TwoXl => "pt-32",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
enum SectionBackground {
    None,
    Light,
    Dark,
    Primary,
    Secondary,
    Success,
    Warning,
    Error,
}

impl SectionBackground {
    fn class_name(&self) -> &'static str {
        match self {
            SectionBackground::None => "",
            SectionBackground::Light => "bg-light",
            SectionBackground::Dark => "bg-dark",
            SectionBackground::Primary => "bg-primary",
            SectionBackground::Secondary => "bg-secondary",
            SectionBackground::Success => "bg-success",
            SectionBackground::Warning => "bg-warning",
            SectionBackground::Error => "bg-error",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
enum SectionElement {
    Section,
    Div,
    Header,
    Footer,
    Main,
    Aside,
    Article,
}

#[component]
pub fn Section(
    #[prop(optional)] spacing: SectionSpacing,
    #[prop(optional)] spacing_top: Option<SectionSpacing>,
    #[prop(optional)] spacing_bottom: Option<SectionSpacing>,
    #[prop(optional)] background: SectionBackground,
    #[prop(optional)] container: bool,
    #[prop(optional)] max_width: ContainerMaxWidth,
    #[prop(optional)] horizontal_padding: ContainerHorizontalPadding,
    #[prop(optional)] container_class_name: Option<String>,
    #[prop(optional, into)] class: String,
    #[prop(optional)] as_element: SectionElement,
    children: Children,
) -> impl IntoView {
    let top = spacing_top.unwrap_or(spacing);
    let bottom = spacing_bottom.unwrap_or(spacing);

    let classes = format!(
        "{} {} {}",
        top.class_name(),
        bottom.class_name(),
        background.class_name()
    );

    view! {
        <Component
            class=classes
            ..props
        >
            {if container {
                view! {
                    <Container
                        maxWidth=max_width
                        horizontalPadding=horizontal_padding
                        class=container_class_name
                    >
                        {children}
                    </Container>
                }
            } else {
                children
            }}
        </Component>
    }
}