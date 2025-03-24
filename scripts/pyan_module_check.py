#!/usr/bin/env python3
"""
A script that uses pyan to analyze Python code dependencies and check if code can be
properly assigned to a specific module based on dependencies.
Adapted for Poetry-based project structure.
"""
import os
import sys
import argparse
import subprocess
import json
from pathlib import Path


def parse_arguments():
    parser = argparse.ArgumentParser(description="Check module assignments using pyan.")
    parser.add_argument(
        "--module", required=True, help="Module to check (e.g., src.util)"
    )
    parser.add_argument("--source-dir", default="src", help="Source directory to scan")
    parser.add_argument(
        "--max-external-deps",
        type=int,
        default=3,
        help="Maximum number of external dependencies allowed",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def run_pyan_analysis(source_dir, module_name):
    """Run pyan and return the analyzed dependencies as a dictionary."""
    try:
        # Find all Python files in the source directory
        python_files = list(Path(source_dir).rglob("*.py"))

        if not python_files:
            print(f"No Python files found in {source_dir}")
            return None

        # Run pyan to analyze the dependencies
        cmd = [
            "pyan",
            "--uses",
            "--no-defines",
            "--colored",
            "--grouped",
            "--annotated",
            "--dot",
            *[str(f) for f in python_files],
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error running pyan: {result.stderr}")
            return None

        # Convert dot output to a more usable format
        graph_data = {}
        for line in result.stdout.splitlines():
            if "->" in line:
                source, target = line.split("->")
                source = source.strip().replace('"', "")
                target = target.split("[")[0].strip().replace('"', "")

                if source not in graph_data:
                    graph_data[source] = []
                graph_data[source].append(target)

        return graph_data

    except Exception as e:
        print(f"Error during pyan analysis: {str(e)}")
        return None


def check_module_assignment(graph_data, module_name, max_external_deps, verbose):
    """
    Check if the module has acceptable dependencies to be considered well-assigned.

    Returns True if the module passes the checks, False otherwise.
    """
    if not graph_data:
        return False

    module_prefix = f"{module_name}."
    module_components = [
        node for node in graph_data.keys() if node.startswith(module_prefix)
    ]

    if not module_components:
        print(f"Module {module_name} not found in the analyzed code")
        return False

    issues = []

    for component in module_components:
        if component not in graph_data:
            continue

        external_deps = [
            target
            for target in graph_data[component]
            if not target.startswith(module_prefix)
            and "." in target  # Filter to include only external module imports
        ]

        if len(external_deps) > max_external_deps:
            issues.append(
                f"{component} has too many external dependencies: {len(external_deps)} > {max_external_deps}"
            )
            if verbose:
                print(f"  External dependencies for {component}:")
                for dep in external_deps:
                    print(f"  - {dep}")

    if issues:
        print(f"Module {module_name} has assignment issues:")
        for issue in issues:
            print(f"- {issue}")
        return False

    print(f"Module {module_name} passes dependency checks")
    return True


def main():
    args = parse_arguments()

    graph_data = run_pyan_analysis(args.source_dir, args.module)
    if not graph_data:
        sys.exit(1)

    is_valid = check_module_assignment(
        graph_data, args.module, args.max_external_deps, args.verbose
    )

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
