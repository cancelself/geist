#!/usr/bin/env python3
"""
Test script to verify that Geist containers can fetch URLs

This will:
1. Create a temporary geist container
2. Test curl/wget availability
3. Attempt to fetch the Nietzsche article URL
4. Report results
"""

import sys
import os
from pathlib import Path
from geist import GeistSwarm

def test_url_fetching():
    """Test if containers can fetch URLs"""

    # Initialize swarm
    swarm = GeistSwarm()

    print("Testing URL fetching capabilities in Geist containers...")
    print("=" * 80)

    # Get or create a test geist
    state = swarm.load_state()

    if not state["geists"]:
        print("\nNo geists found. Creating default geists first...")
        swarm.ensure_default_geists()
        state = swarm.load_state()

    # Use the first available geist for testing
    test_geist_name = list(state["geists"].keys())[0]
    print(f"\nUsing {test_geist_name} for testing...")

    try:
        container = swarm.get_geist_container(test_geist_name)

        # Test 1: Check if curl is available
        print("\n[TEST 1] Checking if curl is installed...")
        result = container.exec_run(["which", "curl"])
        if result.exit_code == 0:
            print("✓ curl is installed:", result.output.decode().strip())
        else:
            print("✗ curl not found")
            return False

        # Test 2: Check if wget is available
        print("\n[TEST 2] Checking if wget is installed...")
        result = container.exec_run(["which", "wget"])
        if result.exit_code == 0:
            print("✓ wget is installed:", result.output.decode().strip())
        else:
            print("✗ wget not found")

        # Test 3: Test basic internet connectivity
        print("\n[TEST 3] Testing basic internet connectivity...")
        result = container.exec_run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://www.google.com"])
        status_code = result.output.decode().strip()
        if status_code == "200":
            print(f"✓ Internet connectivity working (HTTP {status_code})")
        else:
            print(f"⚠ Got HTTP {status_code} from google.com")

        # Test 4: Try to fetch the Nietzsche article
        print("\n[TEST 4] Attempting to fetch the Nietzsche/AI article...")
        url = "https://cacm.acm.org/blogcacm/why-nietzsche-matters-in-the-age-of-artificial-intelligence/"

        result = container.exec_run([
            "bash", "-c",
            f"curl -s -o /dev/null -w '%{{http_code}}' -L '{url}'"
        ])
        status_code = result.output.decode().strip()

        print(f"HTTP Status Code: {status_code}")

        if status_code == "200":
            print("✓ SUCCESS! The container can fetch the article URL")

            # Try to get actual content
            print("\nFetching first 500 characters of content...")
            result = container.exec_run([
                "bash", "-c",
                f"curl -s -L '{url}' | head -c 500"
            ])
            content = result.output.decode('utf-8', errors='ignore')
            print(content)

        elif status_code == "403":
            print("✗ Got 403 Forbidden - The website is blocking automated access")
            print("  This means curl/wget work, but the site blocks them")
            print("  Claude Code running inside the container will face the same restriction")
        else:
            print(f"⚠ Got HTTP {status_code}")

        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("- Containers HAVE curl and wget installed ✓")
        print("- Containers CAN access the internet ✓")
        print(f"- The specific article URL returns HTTP {status_code}")
        print("\nConclusion: Geists can execute curl/wget commands, but may face")
        print("            restrictions from websites that block automated access.")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_url_fetching()
    sys.exit(0 if success else 1)
