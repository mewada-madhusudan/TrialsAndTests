import os
import sys
from pathlib import Path
import subprocess
from typing import List, Dict, Optional
import json

class PylintRunner:
    """A class to run pylint on Python projects and generate reports."""
    
    def __init__(self, project_path: str, config_path: Optional[str] = None):
        """
        Initialize the linter with project path and optional config file.
        
        Args:
            project_path: Path to the project directory
            config_path: Optional path to pylintrc config file
        """
        self.project_path = Path(project_path)
        self.config_path = Path(config_path) if config_path else None
        
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path {project_path} does not exist")
        if self.config_path and not self.config_path.exists():
            raise FileNotFoundError(f"Config file {config_path} does not exist")

    def find_python_files(self) -> List[Path]:
        """Recursively find all Python files in the project directory."""
        python_files = []
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files

    def run_pylint(self, files: List[Path]) -> Dict:
        """
        Run pylint on the specified files.
        
        Args:
            files: List of Path objects pointing to Python files
            
        Returns:
            Dictionary containing lint results
        """
        results = {
            'summary': {
                'total_files': len(files),
                'files_with_issues': 0,
                'total_issues': 0
            },
            'files': {}
        }
        
        cmd = ['pylint', '--output-format=json']
        if self.config_path:
            cmd.extend(['--rcfile', str(self.config_path)])
        
        for file in files:
            try:
                # Run pylint on individual file
                process = subprocess.run(
                    [*cmd, str(file)],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Parse JSON output
                if process.stdout.strip():
                    issues = json.loads(process.stdout)
                    if issues:
                        results['files'][str(file)] = issues
                        results['summary']['files_with_issues'] += 1
                        results['summary']['total_issues'] += len(issues)
                
            except subprocess.SubprocessError as e:
                print(f"Error processing {file}: {e}", file=sys.stderr)
                continue
                
        return results

    def generate_report(self, results: Dict) -> str:
        """
        Generate a readable report from the lint results.
        
        Args:
            results: Dictionary containing lint results
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("Pylint Analysis Report")
        report.append("=" * 20)
        report.append(f"\nSummary:")
        report.append(f"Total files analyzed: {results['summary']['total_files']}")
        report.append(f"Files with issues: {results['summary']['files_with_issues']}")
        report.append(f"Total issues found: {results['summary']['total_issues']}\n")
        
        for file_path, issues in results['files'].items():
            report.append(f"\nFile: {file_path}")
            report.append("-" * 50)
            
            for issue in issues:
                report.append(
                    f"Line {issue['line']}: {issue['message']} "
                    f"({issue['message-id']}, {issue['symbol']})"
                )
        
        return "\n".join(report)

    def run(self) -> str:
        """
        Main method to run the linter and generate a report.
        
        Returns:
            Formatted report string
        """
        python_files = self.find_python_files()
        results = self.run_pylint(python_files)
        return self.generate_report(results)

def main():
    """Command line interface for the pylint runner."""
    if len(sys.argv) < 2:
        print("Usage: python pylint_runner.py <project_path> [config_path]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        runner = PylintRunner(project_path, config_path)
        report = runner.run()
        print(report)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
