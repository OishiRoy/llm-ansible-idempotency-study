DRIFT_RULES = {
    "P02": {
        "category": "Package Management",
        "description": "Remove Git after the desired state has been established.",
        "inject": "apt-get remove -y git",
        "verify_drift": (
            "test \"$(dpkg-query -W -f='${db:Status-Status}' git 2>/dev/null)\" "
            "!= \"installed\""
        ),
        "verify_recovery": (
            "test \"$(dpkg-query -W -f='${db:Status-Status}' git 2>/dev/null)\" "
            "= \"installed\""
        ),
    },

    "P08": {
        "category": "File and Directory Management",
        "description": "Change app.conf permissions from 0644 to 0600.",
        "inject": "chmod 0600 /opt/myapp/app.conf",
        "verify_drift": (
            "test \"$(stat -c '%a' /opt/myapp/app.conf)\" = \"600\""
        ),
        "verify_recovery": (
            "test \"$(stat -c '%a' /opt/myapp/app.conf)\" = \"644\""
        ),
    },

    "P09": {
        "category": "File and Directory Management",
        "description": "Redirect the managed symlink from releases/v2 back to releases/v1.",
        "inject": (
            "rm -f /opt/myapp/current && "
            "ln -s /opt/myapp/releases/v1 /opt/myapp/current"
        ),
        "verify_drift": (
            "test \"$(readlink -f /opt/myapp/current)\" "
            "= \"/opt/myapp/releases/v1\""
        ),
        "verify_recovery": (
            "test \"$(readlink -f /opt/myapp/current)\" "
            "= \"/opt/myapp/releases/v2\""
        ),
    },

      "P14": {
        "category": "User and Access Management",
        "description": "Replace the required SSH key with an incorrect key.",
        "inject": (
            "printf '%s\\n' "
            "'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIWrongKeyForDriftTest appuser@test' "
            "> /home/appuser/.ssh/authorized_keys && "
            "chown appuser:appuser /home/appuser/.ssh/authorized_keys"
        ),
        "verify_drift": (
            "! grep -qx "
            "'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyForResearchOnly appuser@test' "
            "/home/appuser/.ssh/authorized_keys"
        ),
        "verify_recovery": (
            "grep -qx "
            "'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyForResearchOnly appuser@test' "
            "/home/appuser/.ssh/authorized_keys "
            "&& test \"$(wc -l < /home/appuser/.ssh/authorized_keys)\" -eq 1"
        ),
    },

    "P15": {
        "category": "User and Access Management",
        "description": "Change ownership of /opt/myapp away from appuser:appgroup.",
        "inject": "chown root:root /opt/myapp",
        "verify_drift": (
            "test \"$(stat -c '%U:%G' /opt/myapp)\" = \"root:root\""
        ),
        "verify_recovery": (
            "test \"$(stat -c '%U:%G' /opt/myapp)\" = \"appuser:appgroup\""
        ),
    },

    "P19": {
        "category": "Service and Application Configuration",
        "description": "Change nginx worker_connections from 1024 back to 768.",
        "inject": (
            "sed -i -E "
            "'s/worker_connections[[:space:]]+1024;/worker_connections 768;/' "
            "/etc/nginx/nginx.conf"
        ),
        "verify_drift": (
            "grep -Eq '^[[:space:]]*worker_connections[[:space:]]+768;' "
            "/etc/nginx/nginx.conf"
        ),
        "verify_recovery": (
            "grep -Eq '^[[:space:]]*worker_connections[[:space:]]+1024;' "
            "/etc/nginx/nginx.conf"
        ),
    },

    "P21": {
        "category": "System Configuration and Scheduling",
        "description": "Remove APP_ENV=production from /etc/environment.",
        "inject": (
            "sed -i '/^[[:space:]]*APP_ENV=production[[:space:]]*$/d' "
            "/etc/environment"
        ),
        "verify_drift": (
            "! grep -qx 'APP_ENV=production' /etc/environment"
        ),
        "verify_recovery": (
            "grep -qx 'APP_ENV=production' /etc/environment"
        ),
    },

     "P24": {
        "category": "System Configuration and Scheduling",
        "description": "Remove the managed 02:00 backup cron entry.",
        "inject": (
    "crontab -l 2>/dev/null "
    "| sed "
    "-e '/^#Ansible: myapp daily backup$/d' "
    "-e '/^#Ansible: myapp-backup-job$/d' "
    "-e '\\|/usr/local/bin/myapp-backup.sh|d' "
    "| crontab -"
),
        "verify_drift": (
            "! crontab -l 2>/dev/null "
            "| grep -Eq "
            "'^0[[:space:]]+2[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+/usr/local/bin/myapp-backup.sh$'"
        ),
        "verify_recovery": (
            "crontab -l 2>/dev/null "
            "| grep -Ec "
            "'^0[[:space:]]+2[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+/usr/local/bin/myapp-backup.sh$' "
            "| grep -qx '1'"
        ),
    },

     "P27": {
        "category": "State and Deployment Operations",
        "description": "Remove the setup completion marker.",
        "inject": "rm -f /var/lib/myapp/setup.done",
        "verify_drift": "! test -f /var/lib/myapp/setup.done",
        "verify_recovery": "test -f /var/lib/myapp/setup.done",
    },

    "P28": {
        "category": "State and Deployment Operations",
        "description": "Remove the managed /opt/demo-data directory.",
        "inject": "rm -rf /opt/demo-data",
        "verify_drift": "! test -d /opt/demo-data",
        "verify_recovery": "test -d /opt/demo-data",
    },

     "P29": {
        "category": "State and Deployment Operations",
        "description": "Modify the extracted managed file after deployment.",
        "inject": "printf 'drifted\\n' > /opt/app/file1.txt",
        "verify_drift": (
            "grep -qx 'drifted' /opt/app/file1.txt"
        ),
        "verify_recovery": (
            "test -f /opt/app/file1.txt && "
            "grep -qx 'hello' /opt/app/file1.txt"
        ),
    },

    "P30": {
        "category": "State and Deployment Operations",
        "description": "Remove the deployment record after initial creation.",
        "inject": "rm -f /var/lib/myapp/deployment_record.txt",
        "verify_drift": (
            "! test -e /var/lib/myapp/deployment_record.txt"
        ),
        "verify_recovery": (
            "test -s /var/lib/myapp/deployment_record.txt"
        ),
    },
}

SELECTED_DRIFT_TASKS = list(DRIFT_RULES.keys())
