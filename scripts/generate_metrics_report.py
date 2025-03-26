#!/usr/bin/env python3
"""
Code Metrics Report Generator

Processes Radon output to create a focused report on code complexity metrics
with visualizations for GitHub Actions comments.
"""

import json
import os
import sys
import argparse
from datetime import datetime
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO


def get_risk_level(cc, emoji=True):
    """Get risk level based on cyclomatic complexity"""
    if cc <= 5:
        return "🟢 Low" if emoji else "Low"
    elif cc <= 10:
        return "🟡 Moderate" if emoji else "Moderate"
    elif cc <= 20:
        return "🟠 High" if emoji else "High"
    else:
        return "🔴 Very High" if emoji else "Very High"


def format_mi_rank(rank):
    """Format maintainability index rank with emoji"""
    rank_emoji = {"A": "🟢", "B": "🟢", "C": "🟠", "D": "🔴", "F": "🔴"}
    emoji = rank_emoji.get(rank, "⚪")
    return f"{emoji} {rank}"


def create_complexity_bar_chart(module_data, output_path="complexity_chart.png"):
    """Create a bar chart showing top modules by complexity"""
    # Sort and take top 10 modules
    sorted_data = sorted(
        module_data.items(), key=lambda x: x[1]["max_cc"], reverse=True
    )[:10]

    modules = [
        m[0].split("/")[-1] for m in sorted_data
    ]  # Just the filename for readability
    complexities = [m[1]["max_cc"] for m in sorted_data]

    # Create colors based on complexity levels
    colors = []
    for cc in complexities:
        if cc <= 5:
            colors.append("green")
        elif cc <= 10:
            colors.append("yellow")
        elif cc <= 20:
            colors.append("orange")
        else:
            colors.append("red")

    plt.figure(figsize=(10, 6))
    bars = plt.barh(modules, complexities, color=colors)

    # Add complexity values at the end of each bar
    for bar in bars:
        width = bar.get_width()
        plt.text(
            width + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.0f}",
            ha="left",
            va="center",
            fontweight="bold",
        )

    plt.xlabel("Cyclomatic Complexity")
    plt.title("Top 10 Modules by Complexity")
    plt.tight_layout()

    # Save to file
    plt.savefig(output_path)

    # Also return as base64 for embedding in Markdown
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    img_data = base64.b64encode(img_buffer.read()).decode("utf-8")
    plt.close()

    return img_data


def generate_ascii_bar(value, max_value, max_length=40):
    """Generate a simple ASCII bar representation"""
    bar_length = int((value / max_value) * max_length) if max_value > 0 else 0
    return "█" * bar_length


def process_complexity_data(cc_file_path):
    """Process cyclomatic complexity data for report"""
    try:
        if not os.path.exists(cc_file_path) or os.path.getsize(cc_file_path) == 0:
            return {}, 0, 0

        with open(cc_file_path, "r") as f:
            cc_data = json.load(f)

        # Calculate module-level metrics
        module_metrics = {}
        all_complexities = []

        for module, functions in cc_data.items():
            if not functions or not module.endswith(
                (".py", ".js", ".ts", ".java", ".c", ".cpp")
            ):
                continue

            cc_values = [func["complexity"] for func in functions]
            function_names = [func["name"] for func in functions]
            highest_function = ""
            highest_cc = 0

            if cc_values:
                avg_cc = sum(cc_values) / len(cc_values)
                max_cc = max(cc_values)
                all_complexities.extend(cc_values)

                # Find function with highest complexity
                for i, cc in enumerate(cc_values):
                    if cc > highest_cc:
                        highest_cc = cc
                        highest_function = function_names[i]

                module_metrics[module] = {
                    "avg_cc": avg_cc,
                    "max_cc": max_cc,
                    "risk": get_risk_level(max_cc),
                    "highest_function": highest_function,
                }

        avg_complexity = (
            sum(all_complexities) / len(all_complexities) if all_complexities else 0
        )

        # Calculate Cyclomatic Complexity Index (higher is worse)
        # This is a custom metric that weights higher complexities more heavily
        if all_complexities:
            cci = sum(cc**1.5 for cc in all_complexities) / len(all_complexities)
        else:
            cci = 0

        return module_metrics, avg_complexity, cci

    except Exception as e:
        print(f"Error processing complexity data: {e}")
        return {}, 0, 0


def process_maintainability_data(mi_file_path):
    """Process maintainability index data for report"""
    try:
        if not os.path.exists(mi_file_path) or os.path.getsize(mi_file_path) == 0:
            return {}, 0

        with open(mi_file_path, "r") as f:
            mi_data = json.load(f)

        # Calculate module-level metrics
        module_metrics = {}
        all_mi_scores = []

        for module, data in mi_data.items():
            if not module.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp")):
                continue

            mi_score = data["mi"]
            rank = data.get("rank", "N/A")
            all_mi_scores.append(mi_score)

            module_metrics[module] = {"mi_score": mi_score, "rank": rank}

        # Calculate Maintainability Index (average of all module MI scores)
        mi = sum(all_mi_scores) / len(all_mi_scores) if all_mi_scores else 0

        return module_metrics, mi

    except Exception as e:
        print(f"Error processing maintainability data: {e}")
        return {}, 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate focused code complexity metrics report"
    )
    parser.add_argument(
        "--mi-file", required=True, help="Path to maintainability index JSON file"
    )
    parser.add_argument(
        "--cc-file", required=True, help="Path to cyclomatic complexity JSON file"
    )
    parser.add_argument("--output", required=True, help="Path to output report file")
    parser.add_argument(
        "--output-dir", default="metrics_output", help="Directory for generated images"
    )
    parser.add_argument(
        "--date", default=None, help="Report date (YYYY-MM-DD HH:MM:SS format)"
    )
    parser.add_argument(
        "--user", default="GitHub Actions", help="User who generated the report"
    )

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Process data
    module_cc_metrics, avg_complexity, cci = process_complexity_data(args.cc_file)
    module_mi_metrics, mi = process_maintainability_data(args.mi_file)

    # Generate complexity bar chart
    chart_path = os.path.join(args.output_dir, "complexity_chart.png")

    # Only create chart if we have data
    bar_chart_md = ""
    if module_cc_metrics:
        img_data = create_complexity_bar_chart(module_cc_metrics, chart_path)
        bar_chart_md = f"""
## Top 10 Modules by Complexity (Visual)

![Complexity Chart](data:image/png;base64,{img_data})
"""

    # Sort modules by complexity for the table
    sorted_by_cc = sorted(
        module_cc_metrics.items(), key=lambda x: x[1]["max_cc"], reverse=True
    )

    # Create the complexity table
    cc_table = "| Module | Max CC | Avg CC | Risk | Highest Complexity Function |\n|--------|--------|--------|------|-------------------------|\n"

    # Add top 10 modules to table
    for module, metrics in sorted_by_cc[:10]:
        short_module = module.split("/")[-1]  # Use just the filename for readability
        cc_table += f"| {short_module} | {metrics['max_cc']} | {metrics['avg_cc']:.1f} | {metrics['risk']} | `{metrics['highest_function']}` |\n"

    # Use provided date or current date
    current_date = args.date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build the report
    report = f"""# 📊 Code Complexity Report

## Summary Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| Average Cyclomatic Complexity | {avg_complexity:.2f} | Average complexity across all functions |
| Cyclomatic Complexity Index | {cci:.2f} | Weighted complexity score (lower is better) |
| Maintainability Index | {mi:.2f} | Overall maintainability score (higher is better) |

{bar_chart_md}

## Top 10 Most Complex Modules

{cc_table}

## What These Metrics Mean

### Cyclomatic Complexity (CC)
Cyclomatic Complexity measures the number of linearly independent paths through a program's source code. In simpler terms, it counts the number of decision points (if statements, loops, etc.) plus one.

- **1-5**: 🟢 **Low complexity** - Simple, easy to understand and maintain
- **6-10**: 🟡 **Moderate complexity** - Reasonably complex but manageable
- **11-20**: 🟠 **High complexity** - Complex code that may be difficult to understand
- **21+**: 🔴 **Very high complexity** - Highly complex code, consider refactoring

### Maintainability Index (MI)
The Maintainability Index is a composite metric based on cyclomatic complexity, lines of code, and Halstead volume. It ranges from 0 to 100, with higher values indicating better maintainability.

- **100-20**: 🟢 **Highly maintainable** (A-B ranks)
- **19-10**: 🟠 **Moderately maintainable** (C rank)
- **9-0**: 🔴 **Difficult to maintain** (D-F ranks)

### Cyclomatic Complexity Index (CCI)
This is a custom metric that weights higher complexity values more heavily. It helps identify codebases where a few very complex functions may be hidden by the average.

A lower CCI indicates a more maintainable codebase with fewer complexity hotspots.

---
*Generated on: {current_date} by {args.user}*
"""

    # Write the report to file
    with open(args.output, "w") as f:
        f.write(report)

    print(f"Report generated successfully: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
