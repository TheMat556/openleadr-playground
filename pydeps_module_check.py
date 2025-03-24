#!/usr/bin/env python3
"""
A script that uses pydeps to analyze Python code dependencies and check if code can be
properly assigned to a specific module based on dependencies.
Adapted for Poetry-based project structure.
"""
import os
import sys
import argparse
import json
import subprocess
from pathlib import Path


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Check module assignments using pydeps."
    )
    parser.add_argument(
        "--module", required=True, help="Module to check (e.g., src.util)"
    )
    parser.add_argument("--source-dir", default=".", help="Source directory to scan")
    parser.add_argument(
        "--max-circular-deps",
        type=int,
        default=0,
        help="Maximum number of circular dependencies allowed",
    )
    parser.add_argument(
        "--max-fan-out",
        type=int,
        default=5,
        help="Maximum outgoing dependencies per module component",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def run_pydeps_analysis(source_dir, module_name):
    """Run pydeps and return the analysis results."""
    try:
        # Construct the module path based on the src package structure
        module_parts = module_name.split(".")
        if module_parts[0] == "src":
            module_path = os.path.join(source_dir, *module_parts)
        else:
            module_path = os.path.join(source_dir, *module_parts)

        if not os.path.exists(module_path) and not os.path.exists(module_path + ".py"):
            print(f"Module {module_name} not found at {module_path}")
            return None

        # Create a temporary JSON file for output
        output_file = "pydeps_output.json"

        # Run pydeps to analyze the dependencies
        cmd = [
            "pydeps",
            module_path,
            "--show-cycles",  # Show cyclic dependencies
            "--noshow",  # Don't show the graph
            "--max-bacon=10",  # Max dependency depth
            "--json",  # Output in JSON format
            "--output",
            output_file,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error running pydeps: {result.stderr}")
            return None

        # Read the JSON output
        if not os.path.exists(output_file):
            print(f"Pydeps did not generate output file: {output_file}")
            return None

        with open(output_file, "r") as f:
            data = json.load(f)

        # Clean up the temporary file
        try:
            os.remove(output_file)
        except:
            pass

        return data

    except Exception as e:
        print(f"Error during pydeps analysis: {str(e)}")
        return None


def check_module_assignment(
    analysis_data, module_name, max_circular_deps, max_fan_out, verbose
):
    """
    Check if the module has acceptable dependency patterns to be considered well-assigned.

    Returns True if the module passes the checks, False otherwise.
    """
    if not analysis_data:
        return False

    # Convert module name to path format for matching with pydeps output
    module_path_format = module_name.replace(".", "/")

    # Extract nodes and dependencies
    nodes = analysis_data.get("nodes", {})
    deps = analysis_data.get("deps", {})

    module_nodes = {
        name: info
        for name, info in nodes.items()
        if name.startswith(module_path_format)
    }

    if not module_nodes:
        print(f"Module {module_name} not found in the analyzed code")
        return False

    issues = []

    # Check for circular dependencies
    cycles = []
    if "cycles" in analysis_data:
        for cycle in analysis_data["cycles"]:
            # Filter cycles that include our module
            if any(node.startswith(module_path_format) for node in cycle):
                cycles.append(cycle)

    if len(cycles) > max_circular_deps:
        issues.append(
            f"Too many circular dependencies: {len(cycles)} > {max_circular_deps}"
        )
        if verbose:
            for i, cycle in enumerate(cycles[:5]):  # Show at most 5 cycles
                print(f"  - Cycle {i+1}: {' -> '.join(cycle)}")

    # Check fan-out (outgoing dependencies) for each component
    for node_name in module_nodes:
        if node_name in deps:
            outgoing = deps[node_name]
            # Count outgoing dependencies to other modules
            external_deps = [
                d for d in outgoing if not d.startswith(module_path_format)
            ]

            if len(external_deps) > max_fan_out:
                issues.append(
                    f"{node_name} has too many outgoing dependencies: {len(external_deps)} > {max_fan_out}"
                )
                if verbose:
                    print(f"  External dependencies for {node_name}:")
                    for dep in external_deps[:10]:  # Show at most 10 dependencies
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

    analysis_data = run_pydeps_analysis(args.source_dir, args.module)
    if not analysis_data:
        sys.exit(1)

    is_valid = check_module_assignment(
        analysis_data,
        args.module,
        args.max_circular_deps,
        args.max_fan_out,
        args.verbose,
    )

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
