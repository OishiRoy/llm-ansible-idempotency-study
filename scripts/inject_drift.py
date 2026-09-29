"""
P03 drift-injection helper.

Call inject_curl_drift(container) BETWEEN run #1 and run #2 of the P03
experiment. It makes a realistic-looking, deterministically newer curl
version available in the container's local apt index, WITHOUT depending
on real Ubuntu mirrors or the current date. Safe to run offline / in CI.

Usage inside run_experiment.py:

    run_playbook(container, "P03")          # RUN #1
    inject_curl_drift(container)             # <-- new step, P03/P09-only
    run_playbook(container, "P03")          # RUN #2
    diff_state(...)                          # now genuinely meaningful
"""
import subprocess, re, tempfile, os

def _exec(container, cmd):
    """Run a shell command inside the target container (docker exec / lxc exec / etc.
    Replace this with whatever your harness already uses to talk to the container."""
    return subprocess.run(
        ["docker", "exec", container, "bash", "-c", cmd],
        capture_output=True, text=True
    )

def inject_curl_drift(container, repo_path_in_container="/tmp/p03-fakerepo"):
    """
    1. Reads the curl version that is actually installed in the container.
    2. Builds a repackaged .deb with the patch number bumped by exactly 1
       (e.g. 8.5.0-2ubuntu10.8 -> 8.5.0-2ubuntu10.9), so it looks like a
       routine Ubuntu security update, not a synthetic marker.
    3. Publishes it as a tiny local apt repo inside the container and
       points apt at it (highest priority), then refreshes the index.

    After this call, `apt-cache policy curl` inside the container will show
    the bumped version as Candidate -- exactly the situation a naive
    (non-held) playbook re-run would upgrade into.
    """
    r = _exec(container, "dpkg-query -W -f='${Version}' curl")
    current_version = r.stdout.strip()
    if not current_version:
        raise RuntimeError("curl not installed in container before drift injection")

    m = re.match(r"^(.*\.)(\d+)$", current_version)
    if not m:
        raise RuntimeError(f"unexpected curl version format: {current_version}")
    bumped_version = f"{m.group(1)}{int(m.group(2)) + 1}"

    setup = f"""
        set -e
        rm -rf {repo_path_in_container}
        mkdir -p {repo_path_in_container}
        cd {repo_path_in_container}
        apt-get download curl libcurl4t64 libcurl3t64-gnutls 2>/dev/null || \
        apt-get download curl libcurl4 2>/dev/null || apt-get download curl
        for deb in *.deb; do
            pkg=$(dpkg-deb -f "$deb" Package)
            rm -rf extracted
            dpkg-deb -R "$deb" extracted
            sed -i "s/^Version: .*/Version: {bumped_version}/" extracted/DEBIAN/control
            dpkg-deb -b extracted "${{pkg}}_{bumped_version}_amd64.deb"
            rm "$deb"
        done
        rm -rf extracted
        dpkg-scanpackages . /dev/null > Packages
        echo "deb [trusted=yes] file://{repo_path_in_container} ./" \
            > /etc/apt/sources.list.d/p03-drift.list
        apt-get update -qq
    """
    result = _exec(container, setup)
    if result.returncode != 0:
        raise RuntimeError(f"drift injection failed:\n{result.stderr}")

    return {
        "before_version": current_version,
        "injected_version": bumped_version,
    }