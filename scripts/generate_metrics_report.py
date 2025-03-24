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
from collections import Counter

def format_mi_rank(rank):
  """Format maintainability index rank with emoji"""
  rank_emoji = {
    "A": "🟢",
    "B": "🟢",
    "C": "🟠",
    "D": "🔴",
    "F": "🔴"
  }
  emoji = rank_emoji.get(rank, "⚪")
  return f"{emoji} {rank}"

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

def calculate_overall_metrics(mi_file_path, cc_file_path):
  """Calculate overall metrics from both MI and CC data"""
  metrics = {
    "total_modules": 0,
    "avg_mi_score": 0,
    "rank_distribution": Counter(),
    "complexity_distribution": Counter(),
    "highest_complexity": 0,
    "lowest_complexity": float('inf'),
    "avg_complexity": 0,
    "total_complexity": 0,
    "total_functions": 0
  }

  # Process maintainability index data
  try:
    if os.path.exists(mi_file_path) and os.path.getsize(mi_file_path) > 0:
      with open(mi_file_path, "r") as f:
        mi_data = json.load(f)

      # Filter modules
      modules = [(module, data) for module, data in mi_data.items()
                 if module.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp"))]

      if modules:
        metrics["total_modules"] = len(modules)
        mi_scores = [data["mi"] for _, data in modules]
        metrics["avg_mi_score"] = sum(mi_scores) / len(mi_scores) if mi_scores else 0

        # Count rank distribution
        for _, data in modules:
          rank = data.get("rank", "N/A")
          metrics["rank_distribution"][rank] += 1
  except Exception:
    pass

  # Process cyclomatic complexity data
  try:
    if os.path.exists(cc_file_path) and os.path.getsize(cc_file_path) > 0:
      with open(cc_file_path, "r") as f:
        cc_data = json.load(f)

      all_complexities = []
      for module, functions in cc_data.items():
        if not functions or not module.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp")):
          continue

        for func in functions:
          cc = func["complexity"]
          all_complexities.append(cc)
          metrics["complexity_distribution"][get_risk_level(cc, emoji=False)] += 1
          metrics["highest_complexity"] = max(metrics["highest_complexity"], cc)
          metrics["lowest_complexity"] = min(metrics["lowest_complexity"], cc)

      metrics["total_functions"] = len(all_complexities)
      metrics["avg_complexity"] = sum(all_complexities) / len(all_complexities) if all_complexities else 0
      metrics["total_complexity"] = sum(all_complexities)

      # Reset lowest complexity if it's still infinity
      if metrics["lowest_complexity"] == float('inf'):
        metrics["lowest_complexity"] = 0
  except Exception:
    pass

  return metrics

def generate_distribution_bar(distribution, total, max_length=20):
  """Generate a visual bar chart of distribution"""
  if not total:
    return "No data available"

  # Sort by categories (assuming A, B, C, D, F for MI ranks or complexity categories)
  result = ""
  for category, count in sorted(distribution.items()):
    percentage = count / total * 100
    bar_length = int(percentage / 100 * max_length)
    bar = "█" * bar_length
    result += f"{category}: {bar} {count} ({percentage:.1f}%)\n"

  return result

def process_maintainability_data(mi_file_path, show_top=10):
  """Process maintainability index data from Radon output"""
  # Create a summary table with top modules
  summary_table = "| Module | MI Score | Rank |\n|--------|----------|------|\n"
  # Create a full table with all modules
  full_table = "| Module | MI Score | Rank |\n|--------|----------|------|\n"

  try:
    if not os.path.exists(mi_file_path) or os.path.getsize(mi_file_path) == 0:
      return "| No maintainability data available | - | - |\n", ""

    with open(mi_file_path, "r") as f:
      content = f.read().strip()
      if not content:
        return "| Empty maintainability data | - | - |\n", ""

      mi_data = json.loads(content)

    # Filter and sort modules
    modules = [(module, data) for module, data in mi_data.items()
               if module.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp"))]

    if not modules:
      return "| No modules found matching filters | - | - |\n", ""

    # Sort by MI score (higher is better)
    sorted_modules = sorted(modules, key=lambda x: x[1]["mi"], reverse=True)

    # Create summary table with top modules
    for module, data in sorted_modules[:show_top]:
      mi_score = data["mi"]
      rank = data.get("rank", "N/A")
      summary_table += f"| {module} | {mi_score:.1f} | {format_mi_rank(rank)} |\n"

    # Create full table with all modules
    for module, data in sorted_modules:
      mi_score = data["mi"]
      rank = data.get("rank", "N/A")
      full_table += f"| {module} | {mi_score:.1f} | {format_mi_rank(rank)} |\n"

  except Exception as e:
    error_msg = f"| Error processing maintainability data | {str(e)[:30]}... | - |\n"
    return error_msg, ""

  return summary_table, full_table

def process_complexity_data(cc_file_path, show_top=10):
  """Process cyclomatic complexity data from Radon output"""
  # Create a summary table with highest complexity modules
  summary_table = "| Module | Average CC | Highest CC | Risk |\n|--------|------------|------------|------|\n"
  # Create a full table with all modules
  full_table = "| Module | Average CC | Highest CC | Risk |\n|--------|------------|------------|------|\n"

  try:
    if not os.path.exists(cc_file_path) or os.path.getsize(cc_file_path) == 0:
      return "| No complexity data available | - | - | - |\n", ""

    with open(cc_file_path, "r") as f:
      content = f.read().strip()
      if not content:
        return "| Empty complexity data | - | - | - |\n", ""

      cc_data = json.loads(content)

    if not cc_data:
      return "| No complexity data found | - | - | - |\n", ""

    module_metrics = {}
    for module, functions in cc_data.items():
      if not functions or not module.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp")):
        continue

      cc_values = [func["complexity"] for func in functions]
      if cc_values:
        avg_cc = sum(cc_values) / len(cc_values)
        max_cc = max(cc_values)
        module_metrics[module] = {
          "avg_cc": avg_cc,
          "max_cc": max_cc,
          "risk": get_risk_level(max_cc)
        }

    if not module_metrics:
      return "| No modules with complexity metrics found | - | - | - |\n", ""

    # First sort by highest CC (most complex)
    sorted_by_highest = sorted(module_metrics.items(), key=lambda x: x[1]["max_cc"], reverse=True)

    # Create summary table with top complex modules
    for module, metrics in sorted_by_highest[:show_top]:
      summary_table += f"| {module} | {metrics['avg_cc']:.1f} | {metrics['max_cc']} | {metrics['risk']} |\n"

    # Create full table with all modules
    for module, metrics in sorted_by_highest:
      full_table += f"| {module} | {metrics['avg_cc']:.1f} | {metrics['max_cc']} | {metrics['risk']} |\n"

  except Exception as e:
    error_msg = f"| Error processing complexity data | {str(e)[:30]}... | - | - |\n"
    return error_msg, ""

  return summary_table, full_table

def extract_metric_from_file(file_path, search_text):
  """Extract a metric from a text file"""
  try:
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
      return "N/A"

    with open(file_path, "r") as f:
      for line in f.read().splitlines():
        if search_text in line:
          return line.split(":")[1].strip()
  except Exception:
    pass
  return "N/A"

def main():
  parser = argparse.ArgumentParser(description='Generate code metrics report')
  parser.add_argument('--mi-file', required=True, help='Path to maintainability index JSON file')
  parser.add_argument('--cc-file', required=True, help='Path to cyclomatic complexity JSON file')
  parser.add_argument('--cc-avg-file', required=True, help='Path to average complexity file')
  parser.add_argument('--cc-total-file', required=True, help='Path to total complexity file')
  parser.add_argument('--output', required=True, help='Path to output report file')
  parser.add_argument('--date', default=None, help='Report date (YYYY-MM-DD HH:MM:SS format)')
  parser.add_argument('--user', default='GitHub Actions', help='User who generated the report')
  parser.add_argument('--show-top', type=int, default=10, help='Number of top modules to show in summary')

  args = parser.parse_args()

  # Calculate overall metrics first
  overall_metrics = calculate_overall_metrics(args.mi_file, args.cc_file)

  # Process data for individual module tables
  mi_summary, mi_full = process_maintainability_data(args.mi_file, args.show_top)
  cc_summary, cc_full = process_complexity_data(args.cc_file, args.show_top)

  # Get overall metrics from radon command output
  overall_avg_cc = extract_metric_from_file(args.cc_avg_file, "Average complexity")
  overall_total_cc = extract_metric_from_file(args.cc_total_file, "Total complexity")

  # Format rank distribution for display
  rank_dist = generate_distribution_bar(
    overall_metrics["rank_distribution"],
    overall_metrics["total_modules"]
  )

  # Format complexity distribution for display
  complexity_dist = generate_distribution_bar(
    overall_metrics["complexity_distribution"],
    overall_metrics["total_functions"]
  )

  # Use provided date or current date
  current_date = args.date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # Build the report
  report = f"""# 📊 Code Metrics Report

## 📈 Project Overview

| Metric | Value |
|--------|-------|
| Total Modules | {overall_metrics["total_modules"]} |
| Total Functions | {overall_metrics["total_functions"]} |
| Average MI Score | {overall_metrics["avg_mi_score"]:.1f} |
| Average Complexity | {overall_metrics["avg_complexity"]:.1f} |
| Highest Complexity | {overall_metrics["highest_complexity"]} |

### Maintainability Distribution
{rank_dist}

### Complexity Distribution
{complexity_dist}


## 📋 Top Modules by Maintainability

{mi_summary}

<details>
<summary>Show all modules</summary>

{mi_full}

</details>

## 📋 Top Modules by Complexity

{cc_summary}

<details>
<summary>Show all modules</summary>

{cc_full}

</details>

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
  with open(args.output, 'w') as f:
    f.write(report)

  print(f"Report generated successfully: {args.output}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
