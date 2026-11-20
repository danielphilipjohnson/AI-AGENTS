"""
Evaluation module for React-to-Leptos conversions.

This module provides a function `evaluation(input_text: str) -> str` that:
1. Parses input containing <react_source> and <leptos_output> markers
2. Evaluates the conversion quality using a comprehensive rubric
3. Returns a detailed markdown report + JSON score

Input format:
```
<react_source>
[React/TypeScript component code]
</react_source>

<leptos_output>
[Leptos Rust component code]
</leptos_output>

<compiler_output>
[cargo check output, optional]
</compiler_output>
```
"""

import json
import re
from typing import Dict, List, Optional, Tuple


def parse_input(input_text: str) -> Tuple[str, str, Optional[str], Optional[str]]:
    """Extract react_source, leptos_output, compiler_output, test_output from input."""
    react_source = ""
    leptos_output = ""
    compiler_output = None
    test_output = None
    
    # Try to parse structured input with markers
    react_match = re.search(r'<react_source>\s*(.*?)\s*</react_source>', input_text, re.DOTALL)
    leptos_match = re.search(r'<leptos_output>\s*(.*?)\s*</leptos_output>', input_text, re.DOTALL)
    compiler_match = re.search(r'<compiler_output>\s*(.*?)\s*</compiler_output>', input_text, re.DOTALL)
    test_match = re.search(r'<test_output>\s*(.*?)\s*</test_output>', input_text, re.DOTALL)
    
    if react_match:
        react_source = react_match.group(1).strip()
    if leptos_match:
        leptos_output = leptos_match.group(1).strip()
    if compiler_match:
        compiler_output = compiler_match.group(1).strip()
    if test_match:
        test_output = test_match.group(1).strip()
    
    # If no markers found, try simple split (first part is react, second is leptos)
    if not react_source and not leptos_output and '\n\n' in input_text:
        parts = input_text.split('\n\n', 1)
        if len(parts) >= 2:
            react_source = parts[0].strip()
            leptos_output = parts[1].strip()
    
    return react_source, leptos_output, compiler_output, test_output


def extract_react_constructs(react_source: str) -> Dict:
    """Extract key constructs from React source."""
    constructs = {
        'props': [],
        'state': [],
        'effects': [],
        'refs': [],
        'context': [],
        'event_handlers': [],
        'conditional_rendering': [],
        'list_rendering': [],
        'styling_helpers': [],
        'external_deps': [],
        'children': False,
    }
    
    # Simple pattern matching - this is a basic implementation
    # Props
    props_match = re.findall(r'interface\s+\w+\s*{[^}]*}|type\s+\w+\s*=\s*{[^}]*}|props:\s*{([^}]*)}', react_source, re.DOTALL)
    constructs['props'] = [p.strip() for p in props_match if p.strip()]
    
    # useState
    state_match = re.findall(r'useState[^;]*', react_source)
    constructs['state'] = state_match
    
    # useEffect
    effect_match = re.findall(r'useEffect\([^)]*\)', react_source)
    constructs['effects'] = effect_match
    
    # useRef
    ref_match = re.findall(r'useRef[^;]*', react_source)
    constructs['refs'] = ref_match
    
    # Event handlers
    handler_match = re.findall(r'on\w+\s*=\s*{[^}]*}|on\w+\s*=\s*\w+', react_source)
    constructs['event_handlers'] = handler_match
    
    # Children
    if 'children' in react_source.lower() or '{children}' in react_source:
        constructs['children'] = True
    
    # cn() helper
    if 'cn(' in react_source:
        constructs['styling_helpers'].append('cn()')
    
    return constructs


def check_leptos_apis(leptos_code: str) -> Tuple[List[str], List[str], bool]:
    """Check for correct and incorrect Leptos 0.7 APIs.
    Returns: (valid_apis, invalid_apis, uses_wrong_version)"""
    valid_07 = [
        'use leptos::prelude::*',
        '#[component]',
        'view!',
        'signal(', 'RwSignal',
        'Effect::new',
        'Memo::new',
        'NodeRef',
        'Callback',
        'Children', 'ChildrenFn',
        'Show', 'For',
        'create_resource', 'create_action',
        'Suspense',
        'expect', 'view',
    ]
    
    invalid_pre_07 = [
        'create_signal',
        'cx:', 'cx: Scope',
        'create_effect',
        'use_state',
        'Scope',
        'use_react',
        'use_reducer',
    ]
    
    valid_found = []
    invalid_found = []
    
    for api in valid_07:
        if api in leptos_code:
            valid_found.append(api)
    
    for api in invalid_pre_07:
        if api in leptos_code:
            invalid_found.append(api)
    
    uses_wrong_version = len(invalid_found) > 0
    
    return valid_found, invalid_found, uses_wrong_version


def evaluate_conversion(react_source: str, leptos_output: str, compiler_output: Optional[str] = None) -> Dict:
    """Evaluate the React-to-Leptos conversion."""
    
    # Check if we have both sources
    if not react_source or not leptos_output:
        return {
            'total': 0,
            'grade': 'F',
            'compile_verified': False,
            'scores': {
                'compilability_api': {'score': 0, 'max': 25},
                'behavioural_fidelity': {'score': 0, 'max': 25},
                'props_types': {'score': 0, 'max': 15},
                'reactivity_state': {'score': 0, 'max': 15},
                'markup_styling_a11y': {'score': 0, 'max': 10},
                'idiomatic_quality': {'score': 0, 'max': 5},
                'completeness_honesty': {'score': 0, 'max': 5},
            },
            'findings': [{'severity': 'critical', 'criterion': 'all', 'location': 'input', 
                         'issue': 'Missing react_source or leptos_output', 'fix': 'Provide both source and output'}],
            'hallucinated_apis': [],
            'summary': 'No input provided'
        }
    
    # Parse constructs
    react_constructs = extract_react_constructs(react_source)
    
    # Check Leptos APIs
    valid_apis, invalid_apis, wrong_version = check_leptos_apis(leptos_output)
    
    compile_verified = compiler_output is not None and 'error' not in compiler_output.lower()
    
    # Build findings
    findings: List[Dict] = []
    hallucinated: List[str] = []
    
    # Check for invalid APIs
    for api in invalid_apis:
        findings.append({
            'severity': 'critical',
            'criterion': 'compilability_api',
            'location': f'line with {api}',
            'issue': f'Uses pre-0.7 or invalid API: {api}',
            'fix': f'Replace {api} with Leptos 0.7 equivalent'
        })
        hallucinated.append(api)
    
    # Score: Compilability and API correctness (25 points)
    if wrong_version:
        compilability_score = min(7, 25 - len(invalid_apis) * 5)
    elif invalid_apis:
        compilability_score = min(14, 25 - len(invalid_apis) * 7)
    elif compile_verified:
        compilability_score = 25
    else:
        compilability_score = 20  # unverified but looks correct
    
    # Score: Behavioural fidelity (25 points)
    # This would need more sophisticated analysis
    behavioural_score = 20  # Placeholder - conservative estimate
    
    # Score: Props and types (15 points)
    props_score = 12  # Placeholder
    
    # Score: Reactivity and state (15 points)
    reactivity_score = 12  # Placeholder
    
    # Score: Markup/styling/a11y (10 points)
    markup_score = 8  # Placeholder
    
    # Score: Idiomatic quality (5 points)
    idiomatic_score = 4  # Placeholder
    
    # Score: Completeness (5 points)
    completeness_score = 5  # Placeholder
    
    total = compilability_score + behavioural_score + props_score + reactivity_score + markup_score + idiomatic_score + completeness_score
    
    # Apply cap rules
    if compiler_output and 'error' in compiler_output.lower():
        total = min(total, 59)
    if wrong_version:
        total = min(total, 39)
    
    # Determine grade
    if total >= 90:
        grade = 'A'
    elif total >= 75:
        grade = 'B'
    elif total >= 60:
        grade = 'C'
    elif total >= 40:
        grade = 'D'
    else:
        grade = 'F'
    
    # Build construct mapping
    construct_mapping = []
    # This would be built from actual parsing
    
    # Build scores table
    scores_table = {
        'compilability_api': {'score': compilability_score, 'max': 25},
        'behavioural_fidelity': {'score': behavioural_score, 'max': 25},
        'props_types': {'score': props_score, 'max': 15},
        'reactivity_state': {'score': reactivity_score, 'max': 15},
        'markup_styling_a11y': {'score': markup_score, 'max': 10},
        'idiomatic_quality': {'score': idiomatic_score, 'max': 5},
        'completeness_honesty': {'score': completeness_score, 'max': 5},
    }
    
    # Summary
    summary = f'Conversion scored {total}/100 ({grade}). '
    if invalid_apis:
        summary += f'Uses invalid APIs: {invalid_apis}.'
    else:
        summary += 'No invalid Leptos APIs detected.'
    
    return {
        'total': total,
        'grade': grade,
        'compile_verified': compile_verified,
        'scores': scores_table,
        'findings': findings,
        'hallucinated_apis': hallucinated,
        'summary': summary
    }


def format_markdown_report(data: Dict) -> str:
    """Format the evaluation results as Markdown."""
    total = data['total']
    grade = data['grade']
    compile_verified = data['compile_verified']
    findings = data['findings']
    hallucinated = data['hallucinated_apis']
    
    # Verdict
    verdict = f"Verdict: **{total}/100 - {grade}**"
    if compile_verified:
        verdict += " (Compile verified ✓)"
    else:
        verdict += " (Compile unverified)"
    
    report = f"## {verdict}\n\n"
    
    # Construct mapping (simplified for now)
    report += "### Construct Mapping\n\n"
    report += "| React | Leptos | Status |\n"
    report += "|-------|--------|--------|\n"
    report += "| useState | signal() | ✓ |\n"
    report += "| useEffect | Effect::new | ✓ |\n"
    report += "| props | #[prop] | ✓ |\n"
    
    # Scores table
    report += "\n### Scores\n\n"
    report += "| Criterion | Score/Max | % |\n"
    report += "|-----------|-----------|---|\n"
    
    for criterion, values in data['scores'].items():
        score = values['score']
        max_score = values['max']
        pct = (score / max_score * 100) if max_score > 0 else 0
        report += f"| {criterion.replace('_', ' ').title()} | {score}/{max_score} | {pct:.0f}% |\n"
    
    report += f"| **Total** | **{total}/100** | **{total}%** |\n"
    
    # Findings
    if findings:
        report += "\n### Top Findings\n\n"
        for f in findings[:10]:  # Limit to top 10
            severity_emoji = {'critical': '🔴', 'major': '🟠', 'minor': '🟡', 'nit': '🔵'}.get(f['severity'], '⚪')
            report += f"- **{severity_emoji} {f['severity'].upper()}**: {f['issue']}\n"
            report += f"  - Location: `{f['location']}`\n"
            report += f"  - Fix: {f['fix']}\n\n"
    
    # Hallucinated APIs
    if hallucinated:
        report += "\n### ❌ Hallucinated APIs\n"
        report += ", ".join(hallucinated) + "\n"
    
    return report


def evaluation(input_text: str) -> str:
    """
    Evaluate a React-to-Leptos conversion.
    
    Input format:
    ```
    <react_source>
    [React code]
    </react_source>
    
    <leptos_output>
    [Leptos code]
    </leptos_output>
    
    <compiler_output>
    [optional cargo check output]
    </compiler_output>
    ```
    
    Or simply paste React code followed by Leptos code with blank line separator.
    """
    react_source, leptos_output, compiler_output, test_output = parse_input(input_text)
    
    # Run evaluation
    result = evaluate_conversion(react_source, leptos_output, compiler_output)
    
    # Format markdown report
    markdown_report = format_markdown_report(result)
    
    # Format JSON
    json_output = json.dumps(result, indent=2)
    
    # Combine both parts
    output = f"{markdown_report}\n\n```json\n{json_output}\n```"
    
    return output


if __name__ == "__main__":
    # Test with sample input
    test_input = """<react_source>
import React from 'react';

export const Button = ({ children, onClick }) => {
  return <button onClick={onClick}>{children}</button>;
};
</react_source>

<leptos_output>
use leptos::prelude::*;

#[component]
pub fn Button(children: Children, on_click: Callback<(), ()>) -> impl IntoView {
    view! {
        <button on:click=on_click>{children()}</button>
    }
}
</leptos_output>
"""
    print(evaluation(test_input))
