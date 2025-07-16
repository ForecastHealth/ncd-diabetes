#!/usr/bin/env python3
"""
Script to update README.md with the latest Appendix 3 comparison results.
Runs get_appendix_3_comparison.py and updates a dedicated section in the README.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_comparison_script():
    """Run get_appendix_3_comparison.py and capture its output."""
    cmd = [sys.executable, "scripts/get_appendix_3_comparison.py"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running comparison script: {e}")
        print(f"Error output: {e.stderr}")
        return None

def update_readme(comparison_output):
    """Update README.md with the comparison results."""
    readme_path = Path("README.md")
    
    if not readme_path.exists():
        print("Error: README.md not found")
        return False
    
    # Read current README content
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Define section markers
    section_start = "## Appendix 3 Comparison Results"
    section_end = "## "  # Next section starts with ##
    
    # Create the new section content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_section = f"""{section_start}

*Last updated: {timestamp}*

```
{comparison_output}
```

"""
    
    # Check if section already exists
    if section_start in content:
        # Find the start and end of the existing section
        start_idx = content.index(section_start)
        
        # Find the next section (## ) after our section
        remaining_content = content[start_idx + len(section_start):]
        next_section_match = remaining_content.find("\n## ")
        
        if next_section_match != -1:
            # There's another section after ours
            end_idx = start_idx + len(section_start) + next_section_match + 1
            updated_content = content[:start_idx] + new_section + content[end_idx:]
        else:
            # Our section is the last one
            updated_content = content[:start_idx] + new_section
    else:
        # Section doesn't exist, append it to the end
        updated_content = content.rstrip() + "\n\n" + new_section
    
    # Write updated content back to README
    with open(readme_path, 'w') as f:
        f.write(updated_content)
    
    return True

def main():
    print("Updating README.md with Appendix 3 comparison results...")
    
    # Run the comparison script
    print("Running comparison script...")
    comparison_output = run_comparison_script()
    
    if comparison_output is None:
        print("Failed to get comparison results")
        return 1
    
    # Update README
    print("Updating README.md...")
    if update_readme(comparison_output):
        print("README.md updated successfully!")
        print("\nYou can now commit the changes with:")
        print("  git add README.md")
        print("  git commit -m 'Update Appendix 3 comparison results'")
        return 0
    else:
        print("Failed to update README.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())