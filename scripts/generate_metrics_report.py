#!/usr/bin/env python3
"""
Code Metrics Report Generator

Processes Radon output and creates a formatted Markdown report
for GitHub comments.
"""

import json
import os
import sys
import argparse
from datetime import datetime


def format_mi_rank(rank):
    """Format maintainability index rank with emoji"""
    rank_emoji = {"A": "🟢", "B": "🟢", "C": "🟠", "D": "🔴", "F": "🔴"}
    emoji = rank_emoji.get(rank, "⚪")
    return f"{emoji} {rank}"


def get_risk_level(cc):
    """Get risk level based on cyclomatic complexity"""
    if cc <= 5:
        return "🟢 Low"
    elif cc <= 10:
        return "🟡 Moderate"
    elif cc <= 20:
        return "🟠 High"
    else:
        return "🔴 Very High"


def process_maintainability_data(mi_file_path):
    """Process maintainability index data from Radon output"""
    mi_table = "| Module | MI Score | Rank |\n|--------|----------|------|\n"
    try:
        with open(mi_file_path, "r") as f:
            mi_data = json.load(f)

        # Filter and sort modules
        sorted_modules = sorted(
            [
                (module, data)
                for module, data in mi_data.items()
                if module.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp"))
            ],
            key=lambda x: x[1]["mi"],
            reverse=True,
        )[
            :10
        ]  # Top 10 modules

        for module, data in sorted_modules:
            mi_score = data["mi"]
            rank = data.get("rank", "N/A")
            mi_table += f"| {module} | {mi_score:.1f} | {format_mi_rank(rank)} |\n"
    except Exception as e:
        mi_table += f"| Error processing maintainability data | {str(e)} | - |\n"

    return mi_table


def process_complexity_data(cc_file_path):
    """Process cyclomatic complexity data from Radon output"""
    cc_table = "| Module | Average CC | Highest CC | Risk |\n|--------|------------|------------|------|\n"
    try:
        with open(cc_file_path, "r") as f:
            cc_data = json.load(f)

        module_metrics = {}
        for module, functions in cc_data.items():
            if not functions or not module.endswith(
                (".py", ".js", ".ts", ".java", ".c", ".cpp")
            ):
                continue

            cc_values = [func["complexity"] for func in functions]
            if cc_values:
                avg_cc = sum(cc_values) / len(cc_values)
                max_cc = max(cc_values)
                module_metrics[module] = {
                    "avg_cc": avg_cc,
                    "max_cc": max_cc,
                    "risk": get_risk_level(max_cc),
                }

        sorted_modules = sorted(
            module_metrics.items(), key=lambda x: x[1]["max_cc"], reverse=True
        )[:10]

        for module, metrics in sorted_modules:
            cc_table += f"| {module} | {metrics['avg_cc']:.1f} | {metrics['max_cc']} | {metrics['risk']} |\n"
    except Exception as e:
        cc_table += f"| Error processing complexity data | {str(e)} | - | - |\n"

    return cc_table


def extract_metric_from_file(file_path, search_text):
    """Extract a metric from a text file"""
    try:
        with open(file_path, "r") as f:
            for line in f:
                if search_text in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return "N/A"


def main():
    parser = argparse.ArgumentParser(description="Generate code metrics report")
    parser.add_argument(
        "--mi-file", required=True, help="Path to maintainability index JSON file"
    )
    parser.add_argument(
        "--cc-file", required=True, help="Path to cyclomatic complexity JSON file"
    )
    parser.add_argument(
        "--cc-avg-file", required=True, help="Path to average complexity file"
    )
    parser.add_argument(
        "--cc-total-file", required=True, help="Path to total complexity file"
    )
    parser.add_argument("--output", required=True, help="Path to output report file")
    parser.add_argument("--date", default=None, help="Report date (YYYY-MM-DD format)")
    parser.add_argument(
        "--user", default="GitHub Actions", help="User who generated the report"
    )

    args = parser.parse_args()

    # Process data
    mi_table = process_maintainability_data(args.mi_file)
    cc_table = process_complexity_data(args.cc_file)

    # Get overall metrics
    overall_avg_cc = extract_metric_from_file(args.cc_avg_file, "Average complexity")
    overall_total_cc = extract_metric_from_file(args.cc_total_file, "Total complexity")

    # Use provided date or current date
    if args.date:
        current_date = args.date
    else:
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build the report
    report = f"""# 📊 Code Metrics Report

## 🛠️ Metrics Overview

| Metric | Value | Status |
|--------|-------|--------|
| 📈 **Maintainability Index** | Analyzed modules | ✅ Completed |
| 🔄 **Cyclomatic Complexity** | Avg: {overall_avg_cc} / Total: {overall_total_cc} | ✅ Completed |

## 📋 Top Modules by Maintainability

{mi_table}

## 📋 Top Modules by Complexity

{cc_table}

## 📚 Interpretation Guide

- **Maintainability Index (MI)**
  - 100-20: 🟢 Highly maintainable (A-B)
  - 19-10: 🟠 Moderately maintainable (C)
  - 9-0: 🔴 Difficult to maintain (D-F)

- **Cyclomatic Complexity (CC)**
  - 1-5: 🟢 Simple, low risk
  - 6-10: 🟡 Moderate complexity
  - 11-20: 🟠 High complexity
  - 21+: 🔴 Very high complexity, refactor recommended

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
