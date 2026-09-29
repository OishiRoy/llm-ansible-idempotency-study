TASK_RULES = {
    "P01": {
        "setup": [],
        "verify": "dpkg -s nginx"
    },
    "P02": {
        "setup": [],
        "verify": "dpkg -s git"
    },
    "P03": {
    "setup": [],
    "verify": (
        "dpkg -s curl >/dev/null 2>&1 "
        "&& apt-mark showhold 2>/dev/null | grep -Fxq 'curl'"
    )
    },

    "P04": {
    "setup": [],
    "verify": "dpkg -s unzip >/dev/null 2>&1"
   },

    "P05": {
        "setup": [],
        "verify": "! dpkg -s apache2 >/dev/null 2>&1"
    },

    "P06": {
        "setup": [],
        "verify": "test -d /opt/myapp"
    },

    "P07": {
    "setup": [
        "mkdir -p /etc/myapp",
        "printf 'EXISTING_SETTING=yes\\n' > /etc/myapp/app.conf"
    ],
    "verify": (
        "grep -Eq '^[[:space:]]*EXISTING_SETTING=yes[[:space:]]*$' /etc/myapp/app.conf "
        "&& grep -Eq '^[[:space:]]*setting1=value1[[:space:]]*$' /etc/myapp/app.conf "
        "&& grep -Eq '^[[:space:]]*setting2=value2[[:space:]]*$' /etc/myapp/app.conf"
    )
   },

    "P08": {
    "setup": [
        "mkdir -p /opt/myapp",
        "touch /opt/myapp/app.conf",
        "chmod 0600 /opt/myapp/app.conf"
    ],
    "verify": "stat -c %a /opt/myapp/app.conf | grep -qx 644"
   },

    "P09": {
    "setup": [
        "mkdir -p /opt/myapp/releases/v1",
        "mkdir -p /opt/myapp/releases/v2",
        "ln -s /opt/myapp/releases/v1 /opt/myapp/current"
    ],
    "verify": "test \"$(readlink -f /opt/myapp/current)\" = \"/opt/myapp/releases/v2\""
    },

    "P10": {
        "setup": [
            "mkdir -p /etc/myapp",
            "touch /etc/myapp/app.conf"
        ],
        "verify": "grep -qx 'APP_MODE=production' /etc/myapp/app.conf"
    },
    
    "P11": {
        "setup": [],
        "verify": "id appuser"
    },

    "P12": {
        "setup": [],
        "verify": "getent group appgroup"
    },

    "P13": {
        "setup": [
            "getent group appgroup >/dev/null || groupadd appgroup",
            "id appuser >/dev/null 2>&1 || useradd -m appuser"
        ],
        "verify": "id -nG appuser | tr ' ' '\\n' | grep -qx appgroup"
    },

    "P14": {
    "setup": [
        "id appuser >/dev/null 2>&1 || useradd -m appuser",
        "mkdir -p /home/appuser/.ssh",
        "touch /home/appuser/.ssh/authorized_keys",
        "chown -R appuser:appuser /home/appuser/.ssh"
    ],
    "verify": "grep -qx 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyForResearchOnly appuser@test' /home/appuser/.ssh/authorized_keys && test \"$(wc -l < /home/appuser/.ssh/authorized_keys)\" -eq 1"
    },

    "P15": {
        "setup": [
            "getent group appgroup >/dev/null || groupadd appgroup",
            "id appuser >/dev/null 2>&1 || useradd -m appuser",
            "mkdir -p /opt/myapp"
        ],
        "verify": "test \"$(stat -c '%U:%G' /opt/myapp)\" = \"appuser:appgroup\""
    },

    "P16": {
    "setup": [
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get install -y nginx"
    ],
    "verify": "pgrep -x nginx >/dev/null"
    },

    "P17": {
    "setup": [
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get install -y nginx"
    ],
    "verify": "test -L /etc/rc2.d/S01nginx || test -L /etc/systemd/system/multi-user.target.wants/nginx.service"
    },

    "P18": {
    "setup": [
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get install -y nginx",
        "service nginx start",
    ],
    "verify": "! pgrep -x nginx >/dev/null"
    },

    "P19": {
    "setup": [
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get install -y nginx"
    ],
    "verify": "grep -Eq '^[[:space:]]*worker_connections[[:space:]]+1024;' /etc/nginx/nginx.conf"
    },

    "P20": {
    "setup": [],
    "verify": (
        "dpkg -s cron >/dev/null 2>&1 "
        "&& pgrep -x cron >/dev/null"
    )
    },

    "P21": {
        "setup": [],
        "verify": "grep -qx 'APP_ENV=production' /etc/environment"
    },

    "P22": {
    "setup": [
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get install -y nginx",
        "sed -i 's/worker_connections[[:space:]]*[0-9]\\+;/worker_connections 768;/' /etc/nginx/nginx.conf"
    ],
    "verify": "grep -Eq '^[[:space:]]*worker_connections[[:space:]]+1024;' /etc/nginx/nginx.conf"
    }, 

   "P23": {
    "setup": [
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get install -y nginx",
        "mkdir -p /etc/nginx/conf.d"
    ],

    "verify": (
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        "p = Path('/etc/nginx/conf.d/myapp.conf')\n"
        "expected = \"server { listen 8080; server_name localhost; location / { return 200 'myapp'; } }\"\n"
        "text = p.read_text().strip()\n"
        "normalized = ' '.join(text.split())\n"
        "raise SystemExit(0 if normalized == expected else 1)\n"
        "PY"
    )
    },

    "P24": {
    "setup": [
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get install -y cron",
        "printf '#!/bin/sh\\nexit 0\\n' > /usr/local/bin/myapp-backup.sh",
        "chmod +x /usr/local/bin/myapp-backup.sh"
    ],
    "verify": (
        "crontab -l 2>/dev/null "
        "| grep -Ec '^0[[:space:]]+2[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+/usr/local/bin/myapp-backup.sh$' "
        "| grep -qx '1'"
    )
    },

    "P25": {
        "setup": [],
        "verify": 'test "$(cat /etc/timezone)" = "Etc/UTC"'
    },

    "P26": {
    "setup": [
        "cp /etc/hosts /tmp/hosts.backup",
        "umount /etc/hosts",
        "cp /tmp/hosts.backup /etc/hosts",
    ],
    "verify": (
        "grep -Ec '^127\\.0\\.0\\.1[[:space:]]+myapp\\.local$' /etc/hosts "
        "| grep -qx '1'"
    )
    },

    "P27": {
    "setup": [
        "mkdir -p /usr/local/bin /var/lib/myapp",
        "printf '#!/bin/sh\\nmkdir -p /var/lib/myapp\\ntouch /var/lib/myapp/setup.done\\n' > /usr/local/bin/setup-myapp.sh",
        "chmod +x /usr/local/bin/setup-myapp.sh"
    ],
    "verify": "test -f /var/lib/myapp/setup.done"
    },

    "P28": {
        "setup": [],
        "verify": "test -d /opt/demo-data"
    },
    "P29": {
    "setup": [
        "mkdir -p /tmp/archive_src",
        "printf 'hello\\n' > /tmp/archive_src/file1.txt",
        "tar -czf /tmp/myapp.tar.gz -C /tmp/archive_src .",
        "mkdir -p /opt/app"
    ],

    "verify": (
        "test -f /opt/app/file1.txt && "
        "grep -qx 'hello' /opt/app/file1.txt"
    )
   },
    "P30": {
    "setup": [
        "mkdir -p /var/lib/myapp"
    ],
    "verify": "test -s /var/lib/myapp/deployment_record.txt"
    },
}
