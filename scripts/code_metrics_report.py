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
import matplotlib

# Use Agg backend for headless environments like GitHub Actions
matplotlib.use("Agg")
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


def create_complexity_bar_chart(
    module_data, output_path="complexity_chart.png", top_n=15
):
    """Create a bar chart showing top modules by complexity"""
    try:
        print(f"Generating complexity chart with {len(module_data)} modules")

        # Sort and take top n modules
        sorted_data = sorted(
            module_data.items(), key=lambda x: x[1]["max_cc"], reverse=True
        )[:top_n]

        if not sorted_data:
            print("No modules with complexity data found")
            return None

        modules = [
            m[0].split("/")[-1] for m in sorted_data
        ]  # Just the filename for readability
        complexities = [m[1]["max_cc"] for m in sorted_data]

        print(f"Top modules: {modules}")
        print(f"Complexities: {complexities}")

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

        # Create the chart - adjust figure height for more modules
        plt.figure(figsize=(10, 8))
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
        plt.title(f"Top {top_n} Modules by Complexity")
        plt.tight_layout()

        # Save to file
        print(f"Saving chart to {output_path}")
        plt.savefig(output_path)
        print(f"Chart saved successfully")

        plt.close()
        return output_path

    except Exception as e:
        print(f"Error generating chart: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


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
        import traceback

        traceback.print_exc()
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
        import traceback

        traceback.print_exc()
        return {}, 0


def create_text_bar_chart(module_data, top_n=15):
    """Create a text-based bar chart for GitHub comments"""
    if not module_data:
        return "No complexity data available for visualization."

    # Sort and get top n modules by complexity
    sorted_data = sorted(
        module_data.items(), key=lambda x: x[1]["max_cc"], reverse=True
    )[:top_n]

    # Find max complexity for scaling
    max_cc = max(m[1]["max_cc"] for m in sorted_data) if sorted_data else 0

    chart = f"## Top {top_n} Modules by Complexity\n\n```\n"

    # Create bars
    for module, metrics in sorted_data:
        short_name = module.split("/")[-1]  # Just the filename for readability
        cc = metrics["max_cc"]
        bar = generate_ascii_bar(cc, max_cc, 40)
        risk_indicator = ""

        if cc <= 5:
            risk_indicator = "🟢"
        elif cc <= 10:
            risk_indicator = "🟡"
        elif cc <= 20:
            risk_indicator = "🟠"
        else:
            risk_indicator = "🔴"

        # Format: filename [bar] value risk
        chart += f"{short_name:<30} {bar} {cc:>3} {risk_indicator}\n"

    chart += "```\n"
    return chart


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
    parser.add_argument(
        "--top-n", type=int, default=15, help="Number of top modules to show"
    )

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Process data
    module_cc_metrics, avg_complexity, cci = process_complexity_data(args.cc_file)
    module_mi_metrics, mi = process_maintainability_data(args.mi_file)

    # Generate complexity chart
    chart_path = os.path.join(args.output_dir, "complexity_chart.png")

    # Create a text-based chart that works in GitHub comments
    text_chart = create_text_bar_chart(module_cc_metrics, args.top_n)

    # Try to create image chart for artifacts
    image_chart_created = False
    try:
        image_path = create_complexity_bar_chart(
            module_cc_metrics, chart_path, args.top_n
        )
        image_chart_created = image_path is not None
        if image_chart_created:
            print(f"Image chart created at {image_path}")
    except Exception as e:
        print(f"Warning: Failed to create image chart: {e}")

    # Sort modules by complexity for the table
    sorted_by_cc = sorted(
        module_cc_metrics.items(), key=lambda x: x[1]["max_cc"], reverse=True
    )

    # Create the complexity table
    cc_table = "| Module | Max CC | Avg CC | Risk | Highest Complexity Function |\n|--------|--------|--------|------|-------------------------|\n"

    # Add top N modules to table
    for module, metrics in sorted_by_cc[: args.top_n]:
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

{text_chart}

## Top {args.top_n} Most Complex Modules

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
