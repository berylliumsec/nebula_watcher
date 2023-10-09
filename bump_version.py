import re
import sys
with open("setup.py", "r") as f:
    content = f.read()

# Extract the current version
match = re.search(r'version=\'([\d.]+)\'', content)
if match:
    version_parts = match.group(1).split('.')
    
    # Increment the last segment of the version number (patch version)
    version_parts[-1] = str(int(version_parts[-1]) + 1)
    new_version = '.'.join(version_parts)

    content = content.replace(f'version=\'{match.group(1)}\'', f'version=\'{new_version}\'')

    print("Updated to new version:")
    print(f"{new_version}")
    with open("setup.py", "w") as f:
        f.write(content)

    # Output the new version for subsequent GitHub Actions steps
    print(f"::set-output name=new_version::{new_version}")
    new_version_file = "new_version.txt"
    with open(new_version_file, "w") as f:
        f.write(new_version)
else:
    print("Version pattern not found!")
    sys.exit(1)
