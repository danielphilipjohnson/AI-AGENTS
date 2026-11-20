# React to Leptos Conversion Prompt

**Role:** You are an expert Rust and Leptos developer. Convert the following React (TypeScript/TSX) component to idiomatic Leptos 0.7.

TARGET
- Leptos 0.7 only. Start with `use leptos::prelude::*;`
- There is no `Scope`/`cx` parameter. Do not use `#[derive(Props)].`
- Props are plain parameters on a `#[component]` function.
- Dependencies available: `leptos = "0.7"` and `tailwind_fuse`. Do not use other crates.

HARD RULES
- Use only APIs you are certain exist in Leptos 0.7 and the std library. Never invent types or macro syntax.
- Preserve behaviour and class strings exactly. Do not rename, reorder or "improve" classes.
- Preserve declaration order. Enum variants must appear in the same order as the TypeScript union members.
- Rust has no default parameter values. Use `#[prop(optional)]` or `#[prop(default = expr)].`

MAPPING RULES
- String-literal unions become enums deriving `Debug, Clone, Copy, PartialEq, Eq, Default`.
- `Record<Union, string>` lookup maps become an `impl` method on the enum returning `&'static str`.
- Optional props: `#[prop(optional)] name: T` where `T: Default`.
- String props: `#[prop(optional, into)] class: String`.
- `children?: ReactNode` becomes `children: Children` or `Option<Children>`.
- `useState` -> `signal()`/`RwSignal`, `useMemo` -> `Memo`, `useEffect` -> `Effect`, callbacks -> `Callback<T>`.
- `...props` / `React.HTMLAttributes`: expose specific attributes (`id`, `style`, `aria-*`).
- `cn(...)`: use `tailwind_fuse::tw_merge!` if caller class overrides matter, otherwise plain concatenation.

RENDERING
- Render with `view! { ... }` only. The macros `html!`, `rsx!`, `jsx!` and `yew::html!` do not exist in Leptos 0.7.
- Class attribute: `<div class=classes>`. Children: `{children()}`, or `{children.map(|c| c())}` when `Option<Children>`.
- Compute class strings in a `let` above `view!`, not inline in the macro.

PROPS
- TSX destructuring default (`cols = 2`): use `#[prop(default = 2)]`. Do not also add `optional`.
- TSX `?` with no default: `#[prop(optional)]`.
- `children?: ReactNode` is `#[prop(optional)] children: Option<Children>`. Required `children` is `children: Children`.
- `number` props: `u32`.
- The `#[default]` variant is the one matching the TypeScript default, which may not be the first variant. Keep the variants in source order anyway.
- Enums and components are `pub`.

HELPERS AND SOURCE BUGS
- Lookup tables and helpers are module-level functions, never defined inside a component. Use `match` returning `&'static str`.
- Every binding must be used.

EXAMPLE OF A CORRECT SIGNATURE
```rust
#[component]
pub fn Container(
    #[prop(optional)] max_width: ContainerMaxWidth,
    #[prop(optional)] horizontal_padding: ContainerHorizontalPadding,
    #[prop(optional, into)] class: String,
    children: Children,
) -> impl IntoView {
```

OUTPUT
- A single ```rust code block, then nothing else.
- Comments only for TODOs and the cn() decision.
- If cannot be converted faithfully, reply exactly: NEEDS-HUMAN: <one-line reason>


**Constraints:**
- Output ONLY the Leptos Rust code, no explanation, no markdown fences
- Use Leptos 0.7 syntax
- Match the component's props interface exactly
- Preserve all functionality (events, effects, children)
- Use `leptos::prelude::*` imports
- Snake case for Rust identifiers (PascalCase React → snake_case Rust)
- Use `#[component]` macro on the component function
- If you cannot convert faithfully, reply exactly: NEEDS-HUMAN: <one-line reason>


**Input React Component:**
```tsx
{react_code}
```

**Output Leptos Component:**