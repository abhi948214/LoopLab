#!/usr/bin/env python3
"""One-time generator for Linux_Networking_SRE_Mastery.md (run if regenerating structure)."""
from pathlib import Path

OUT = Path(__file__).parent / "Linux_Networking_SRE_Mastery.md"


def cmd(title: str, meaning: str, flags: str, examples: str, output: str, war: str) -> str:
    return f"""
### Command reference: `{title}`

**1. Command name & plain English meaning**  
{meaning}

**2. Most frequent production flags**  
{flags}

**3. Concrete command examples**

```bash
{examples.strip()}
```

**4. Interpreting the output (outage triage)**  
{output}

**5. Real-world production war story**  
{war}

---
"""


def main() -> None:
    parts: list[str] = []
    parts.append(
        """# Linux & Networking SRE Mastery Handbook

> **Audience:** SREs targeting high-scale product companies (PhonePe, Razorpay, CRED, Netflix).  
> **Scope:** Kernel fundamentals → live packet-level incident triage.  
> **Convention:** Every operational command uses the five-part production format below.

---

## Table of contents

1. [Module 1 — Linux OS & core architecture](#module-1--the-linux-operating-system--core-systems-architecture)
2. [Module 2 — Essential commands & triage tooling](#module-2--essential-linux-commands--triage-tooling)
3. [Module 3 — Networking fundamentals (OSI → sockets)](#module-3--linux-networking-fundamentals-osi-to-socket-layer)
4. [Module 4 — SRE network diagnostic toolkit](#module-4--the-sre-network-diagnostic-toolkit)
5. [Module 5 — Top 30 interview questions](#module-5--top-30-sre-linux--networking-interview-questions)
6. [Module 6 — 14-day hands-on study plan](#module-6--step-by-step-14-day-hands-on-study--terminal-practice-plan)

---

## Module 1: The Linux Operating System & Core Systems Architecture

### Kernel space vs user space

| Layer | Ring | What runs here | SRE relevance |
|-------|------|----------------|---------------|
| **Kernel space** | Ring 0 | Scheduler, VM, VFS, TCP/IP stack, drivers | Latency spikes, soft lockups, `D` state, conntrack, drops |
| **User space** | Ring 3 | Applications, language runtimes, agents | Thread pools, FD leaks, misconfigured ulimits |

**System calls** are the controlled gateway from Ring 3 → Ring 0. Tracing tools (eBPF, `strace`, `audit`) hook **`sys_enter` / `sys_exit`** tracepoints to observe syscall rate, errors, and latency without recompiling the kernel.

**Context switches** occur when the CPU moves from one runnable entity to another (process/thread). High **cswch/s** with flat CPU can mean lock contention, I/O wait, or oversubscribed workers—not necessarily “high CPU.”

### Process & thread management

| State | Symbol | Meaning | Outage signal |
|-------|--------|---------|----------------|
| Running | `R` | On CPU or runnable | CPU-bound hot loops |
| Interruptible sleep | `S` | Waiting (I/O, lock, poll) | Normal idle; huge counts → backlog |
| Uninterruptible sleep | `D` | Blocked in kernel (often disk/NFS) | **Load avg ↑ while CPU low** |
| Zombie | `Z` | Exited but not reaped | Parent bug; PID exhaustion risk |
| Stopped | `T` | Job control / debugger | Deployments stuck |

**PID 1 (`systemd`)** reaps orphaned children, mounts namespaces, and owns default cgroup hierarchies. If PID 1 is unhealthy, *everything* downstream looks “mysteriously broken.”

**`fork()`** duplicates the calling process (copy-on-write). **`execve()`** replaces the address space with a new program. Shell pipelines and container entrypoints are literally `fork` + `execve` choreography.

### The `/proc` virtual filesystem

`/proc` is not on disk—it is live kernel state exported as files.

| Path | What it tells you |
|------|-------------------|
| `/proc/cpuinfo` | Model, cores, flags (AES-NI, etc.) |
| `/proc/meminfo` | Detailed RAM breakdown (see Module 2 `free`) |
| `/proc/sys/net/` | Tunables: `ipv4/tcp_*`, `core/somaxconn`, conntrack |
| `/proc/<pid>/fd/` | Open FDs (sockets, files, pipes) |
| `/proc/<pid>/status` | `VmRSS`, `Threads`, `FDSize`, `State` |
| `/proc/<pid>/net/tcp` | Socket table in hex (local/remote IP:port, state) |

**Reading `/proc/<pid>/net/tcp`:** Columns include local address, remote address, state. State `01` = ESTABLISHED, `0A` = LISTEN (see kernel `tcp_states`).

```bash
# Decode listening sockets for PID 1234
sudo ls -l /proc/1234/fd | grep socket
sudo cat /proc/1234/net/tcp
grep -i somaxconn /proc/sys/net/core/somaxconn
```

### File descriptors & inodes

Linux **“everything is a file”**: regular files, directories, sockets, pipes, epoll fds, timerfds.

| Limit | Scope | Config |
|-------|-------|--------|
| **Soft ulimit** | Per-process, enforceable at runtime | `ulimit -n`, `/etc/security/limits.conf` |
| **Hard ulimit** | Ceiling for soft limit | root can raise soft up to hard |

**`Too many open files`** during peak traffic is almost always: connection leak, missing `close()`, or default `1024` ulimit on a payment API.

```bash
# Per-service limits (systemd)
systemctl show payment-api -p LimitNOFILE
cat /proc/$(pgrep -f payment-api | head -1)/limits | grep "open files"
```

**Inodes** index metadata. You can have free **blocks** but zero free **inodes** → creates fail with “No space left on device.”

### Memory mechanics

| Term | Meaning |
|------|---------|
| **Virtual memory (VSZ)** | Address space reserved |
| **RSS** | Pages actually in RAM |
| **Page cache** | File-backed cache (reclaimable) |
| **Dirty pages** | Modified cache not yet flushed to disk |
| **Swap** | Paged-out anonymous memory—latency cliff on burst |

**OOM Killer** triggers when reclaim fails. It scores processes via **`oom_score`**; SREs protect critical daemons with **`oom_score_adj`** (-1000 to +1000, lower = safer).

```bash
# Protect kubelet (example)
echo -500 | sudo tee /proc/$(pgrep kubelet)/oom_score_adj
cat /proc/$(pgrep kubelet)/oom_score
```

> **Callout — Bar Raiser expectation:** Strong candidates explain *why* `available` in `free` matters more than `free` column, and why `D` state inflates load average without consuming CPU.

---

"""
    )

    # MODULE 2 COMMANDS
    commands_m2 = [
        (
            "uptime",
            "Shows how long the system has been running and the **load averages** (1/5/15 minutes)—a smoothed count of threads wanting CPU or stuck in uninterruptible I/O.",
            "- *(no flags)* — default load averages\n- `-p` — pretty-print uptime (some distros)",
            "uptime\nuptime -p",
            "Compare **load average** to **CPU count** (`nproc`). If 1-min load is 32 on 16 cores, you are saturated or I/O blocked. Pair with `mpstat` and `ps` for `D` state.",
            "Payment reconciliation batch started at 02:00; load hit 40 on 16-core DB nodes while CPU was ~15%. Root cause: NFS-backed storage put dozens of threads in **`D` state**—not CPU. Moved scratch to local SSD; load normalized in minutes.",
        ),
        (
            "top",
            "Interactive **process table** sorted by CPU by default—first screen during “something is slow.”",
            "- `-b` — batch mode (for logs)\n- `-H` — show threads\n- `-p PID` — monitor specific PIDs\n- `-o %MEM` — sort by memory",
            "top -H -p $(pgrep -f payment-api)\ntop -b -n 1 | head -30",
            "Watch **`%CPU`**, **`RES`**, **`S` column** (state), **`TIME+`**. One thread at 100% → hot loop; many threads in `S` → wait on lock/I/O.",
            "API p99 doubled; `top -H` showed 200 threads blocked in `S` on same Java process—thread pool queue full. Increased pool *after* fixing downstream Redis timeouts (real bottleneck).",
        ),
        (
            "htop",
            "User-friendly **`top`** with per-CPU bars, tree view, and mouse support—faster situational awareness in war rooms.",
            "- `-p PID` — highlight PIDs\n- `-t` — tree view (install variant dependent)\n- `-d SEC` — delay between updates",
            "htop -p $(pgrep -f nginx | tr '\\n' ',')\nhtop -d 2",
            "Per-CPU saturation vs single-core hot spot. Tree view exposes **parent/child** (worker master → workers).",
            "During Diwali peak, one nginx worker at 100% while others idle—`SO_REUSEPORT` misconfigured. `htop` tree made skew obvious; fixed upstream hash policy.",
        ),
        (
            "mpstat -P ALL 1",
            "**Per-CPU utilization** from `sysstat`—separates user/system/iowait/steal—essential on NUMA and noisy-neighbor VMs.",
            "- `-P ALL` — every CPU\n- `1` — 1-second interval\n- `-u` — CPU report (default)\n- `-I SUM` — interrupt stats",
            "mpstat -P ALL 1 5\nmpstat -I SUM 1 3",
            "**`%iowait`** high → disk/network storage. **`%steal`** high on cloud → hypervisor contention. One CPU at 100% others idle → pinning/lock issue.",
            "Kafka broker “slow” but CPU looked fine on average—`mpstat` showed **single core pegged** on IRQ-heavy NIC queue. RSS/RPS tuning spread load.",
        ),
        (
            "pidstat -u 1",
            "**Per-process CPU** over time—better than one-shot `ps` for proving which PID burned CPU during an incident window.",
            "- `-u` — CPU\n- `-r` — memory\n- `-w` — context switches\n- `-p PID` — filter\n- `1` — interval seconds",
            "pidstat -u 1 10\npidstat -w -p $(pgrep java) 1 5",
            "Watch **`%CPU`**, **`cswch/s`** (voluntary), **`nvcswch/s`** (involuntary). High involuntary → preemption/CPU starvation.",
            "Microservice regression after deploy: `pidstat` tied 80% CPU to one PID; roll back while strace confirmed tight retry loop on 404 from config service.",
        ),
        (
            "free -m",
            "Reports **memory and swap** in megabytes—interpret **`available`**, not just `free`.",
            "- `-m` — megabytes\n- `-h` — human readable\n- `-w` — wide view (separate cache columns on newer procps)",
            "free -m\nfree -wh",
            "**`available`** ≈ memory for new workloads without swapping. Low available + rising **`si/so`** in `vmstat` → swap storm incoming.",
            "Node flapped during batch job; `free` showed 200MB ‘free’ but **only 150MB available**—page cache was huge but not reclaimable fast enough; OOM killed sidecar first.",
        ),
        (
            "vmstat 1",
            "**System-wide counters** each second: processes, memory, swap, I/O, CPU—classic “is it CPU, memory, or disk?” triage.",
            "- `1` — interval\n- `-S M` — megabyte units\n- `-w` — wide",
            "vmstat 1 20\nvmstat -w 1 10",
            "**`r`** runnable queue; **`b`** uninterruptible; **`si/so`** swap in/out; **`wa`** I/O wait CPU%; **`id`** idle.",
            "Checkout latency: `vmstat` showed **`b=12`** constantly—disk/NFS **`D` state**. Storage team found saturated array; not application GC.",
        ),
        (
            "df -h",
            "Shows **filesystem space usage** per mount—first check when writes fail.",
            "- `-h` — human sizes\n- `-T` — fstype\n- `-i` — **inode** usage (critical)\n- `--output=source,fstype,size,used,avail,pcent,target`",
            "df -hT\ndf -i /var",
            "**100%** on any mount stops writes. **`df -h` OK but full errors** → check **`df -i`** and **`lsof +L1`**.",
            "Log shipper stopped; `/var` at 45% blocks but **inodes 100%**—millions of tiny temp files. Cleanup + log rotation fix.",
        ),
        (
            "iostat -xz 1",
            "**Disk I/O statistics**—find saturated devices (`%util`, `await`).",
            "- `-x` — extended stats\n- `-z` — omit idle devices\n- `-d` — device only\n- `1` — interval",
            "iostat -xz 1 10\niostat -xmd 1 5",
            "**`%util` ~100** → device saturated. **`await`** ms high → latency. **`r/s`/`w/s`** with high await → backlog.",
            "DB checkpoint storm: **`nvme0n1` await 80ms**, util 99%. Throttled checkpoint + moved WAL to faster volume; p99 query latency recovered.",
        ),
        (
            "iotop -oP",
            "Shows **which processes** drive disk I/O—`iotop` needs root or capabilities.",
            "- `-o` — only active I/O\n- `-P` — processes (not threads)\n- `-a` — accumulated I/O\n- `-d SEC` — delay",
            "sudo iotop -oP -d 2\nsudo iotop -oPa",
            "Identify unexpected **`java`** or **`rsync`** during peak. **`DISK WRITE`** spikes during deploy often = heap dumps or bad logging.",
            "Mystery SSD wear: `iotop` showed backup agent scanning entire disk hourly—disabled on prod tier.",
        ),
        (
            "lsof +L1",
            "Lists **open files**; **`+L1`** finds **deleted files still held open** (space not reclaimed).",
            "- `-p PID` — process\n- `-i :443` — network\n- `+L1` — link count <1 (deleted but open)\n- `-nP` — no DNS/port names",
            "sudo lsof +L1 | head\nsudo lsof -p $(pgrep java) | wc -l",
            "Deleted file with large size and **PID** still writing → **`df` shows used space** until process closes FD or restarts.",
            "“Disk full” alert but `df` 50%: **`/var/log/app.log (deleted)`** held by app at 200GB. Rolling restart freed space instantly.",
        ),
        (
            "strace",
            "Traces **system calls**— proves what a process *actually* asks the kernel (connect, read, futex, etc.).",
            "- `-p PID` — attach\n- `-f` — follow threads\n- `-e trace=network,file` — filter\n- `-T` — syscall time\n- `-tt` — timestamps\n- `-y` — print paths",
            "sudo strace -fp $(pgrep -f payment-api) -e trace=network -T -tt\nsudo strace -c -p PID  # summary",
            "**Stuck on `connect()`** → network/DNS. **`EAGAIN` on read** → non-blocking wait. **`futex(... FUTEX_WAIT`** → lock/thread pool.",
            "Intermittent 5s timeouts: strace showed **`connect` taking 5003ms** to internal LB—SYN not answered. Network team found security group drift, not app thread pool.",
        ),
        (
            "ps aux --sort=-%mem",
            "Snapshot of **all processes**—sort by memory to find OOM candidates.",
            "- `aux` — all users, BSD format\n- `--sort=-%mem` — top memory\n- `-L` — threads\n- `-o pid,ppid,cmd,%mem,rss` — custom columns",
            "ps aux --sort=-%mem | head -20\nps -eo pid,stat,cmd | awk '$2 ~ /D/ {print}'",
            "**`STAT` contains `D`** → I/O blocked. **`RSS`** large + **`Ssl`** java → heap/off-heap pressure.",
            "Pre-OOM: top 3 Java pods at 92% memory limit—HPA scaled on CPU only; added memory-based scaling and fixed leak in cache map.",
        ),
        (
            "systemctl",
            "Controls **systemd units**—how services start, restart, and log on modern Linux.",
            "`status UNIT` — health + recent logs\n`restart UNIT` — bounce service\n`mask UNIT` — prevent start (break-glass)\n`show UNIT -p ActiveState,SubState`",
            "systemctl status nginx\nsystemctl restart payment-api\nsystemctl show kubelet -p LimitNOFILE,MemoryMax",
            "**`failed (Result: exit-code)`** → check `journalctl -u`. **`activating (auto-restart)`** → crash loop. **`masked`** → intentional disable.",
            "Deploy “succeeded” but traffic 503: unit **`ActiveState=activating`**—bad ExecStart path. `systemctl status` showed exit 203/EXEC in 2 seconds.",
        ),
        (
            "journalctl",
            "Reads **systemd journal**—kernel, service, and structured logs with powerful filters.",
            "- `-u UNIT` — unit logs\n`-k` — kernel\n`-p err` — priority\n`--since \"1 hour ago\"`\n`-f` — follow\n`-o json-pretty`",
            "journalctl -u payment-api --since \"2026-10-01 18:00\" -p warning\njournalctl -k -b -1  # previous boot kernel",
            "Correlate **timestamps** with metrics. **`--boot -1`** for post-mortems after reboot. Kernel **`nf_conntrack: table full`** appears here with `-k`.",
            "Midnight incident: `journalctl -k` showed **NIC link flaps** aligned with TCP retrans spike—datacenter switch port error counters confirmed bad cable.",
        ),
    ]

    parts.append("\n## Module 2: Essential Linux Commands & Triage Tooling\n\n")
    for c in commands_m2:
        parts.append(cmd(*c))

    parts.append(
        """
## Module 3: Linux Networking Fundamentals (OSI to Socket Layer)

### Journey of a packet (curl → wire)

1. **User space:** Application calls `write()` on a connected TCP socket; libc wraps **`sendmsg()`** syscall.
2. **Kernel TCP:** Segments data, applies congestion window, enqueues **`sk_buff`** chains in socket send buffer.
3. **IP layer:** Routing lookup (`FIB`), TTL, DF bit for PMTU, optional XFRM if IPsec.
4. **NIC driver:** DMA from ring buffer; **`ethtool -S`** exposes drops if ring overrun.
5. **Reverse path:** NIC → NAPI polling → netfilter/conntrack → socket receive queue → **`read()`** in app.

### TCP internals for SRE

**3-way handshake:** `SYN` → `SYN-ACK` → `ACK`. **Teardown:** `FIN`/`ACK` exchange (often four segments with simultaneous close variants).

| State | Meaning | Action |
|-------|---------|--------|
| `LISTEN` | Accept queue active | Check `ss -lnt` Recv-Q vs `somaxconn` |
| `ESTABLISHED` | Data flow | If slow, check RTT/retrans |
| `TIME_WAIT` | Closed side waits 2×MSL | Normal on high churn clients; tune only with measurement |
| `CLOSE_WAIT` | Peer sent FIN; app never closed | **Application FD leak** |

**Buffers & congestion:** Send/receive windows, window scaling (`TCP window scaling` option), Reno/Cubic/BBR behavior. **Zero-window** probes in `tcpdump` mean receiver starved.

### DNS architecture

Resolution path (glibc): **`/etc/nsswitch.conf`** (`hosts: files dns`) → **`/etc/hosts`** → **`/etc/resolv.conf`** (or **`systemd-resolved`** via stub **`127.0.0.53`**).

| Record | Purpose |
|--------|---------|
| A / AAAA | IPv4 / IPv6 address |
| CNAME | Alias (cannot coexist with other data at same name) |
| PTR | Reverse lookup |
| SRV | Service discovery |
| TXT | SPF, verification, feature flags |

**TTL caching:** Stale records after cutover cause “split brain” clients. **EDNS0** enables larger responses; truncation → fallback to TCP.

> **Production tip:** Always compare **`dig @resolver`** vs **`dig @authoritative`** during DNS incidents.

---

"""
    )

    commands_m4 = [
        (
            "ss",
            "Modern **socket statistics**—replaces `netstat`, faster on machines with tens of thousands of connections.",
            "- `-t` TCP\n- `-u` UDP\n- `-l` listening\n- `-n` numeric\n- `-p` process\n- `-s` summary\n- `-i` internal TCP info",
            "ss -tulnp\nss -s\nss -ltn '( sport = :8080 )'",
            "**Recv-Q** on LISTEN = completed handshake queue backlog. **Send-Q** high on ESTAB → app not reading or network stuck.",
            "SYN flood symptoms: **`ss -s`** shows **`synrecv`** high; **`Recv-Q`** on listener at **`somaxconn`**. Raised backlog + fixed app accept loop.",
        ),
        (
            "netstat",
            "Legacy **socket listing**—still seen on older runbooks; prefer `ss` on RHEL8+/Ubuntu 22+.",
            "- `-tulnp` — TCP/UDP listen numeric process\n- `-s` — protocol summaries\n- `-c` — continuous",
            "netstat -tulnp\nnetstat -s | grep -i listen",
            "Same semantics as `ss`; if numbers disagree, check namespace (`ip netns exec`).",
            "Vendor script required `netstat`; used it in init container, migrated to `ss` on host for speed at 80k connections.",
        ),
        (
            "dig +trace",
            "**DNS lookup** with delegation tracing—shows which nameserver answers at each level.",
            "`+trace` — iterative path\n`+short` — answer only\n`@server` — force resolver\n`+ttlunits` — human TTL",
            "dig +trace api.bank.com\ndig @8.8.8.8 +short A api.bank.com\ndig +dnssec +multi api.bank.com",
            "Compare **ANSWER vs AUTHORITY** sections. **Unexpected CNAME chains** add latency. **SERVFAIL** → upstream or lame delegation.",
            "Post-migration, 1% clients hit old IP: **`dig +trace`** showed stale NS at registrar—not app bug.",
        ),
        (
            "nslookup",
            "Interactive **DNS query** tool—quick checks; less script-friendly than `dig`.",
            "- `type=MX|TXT|SRV`\n- `server IP` — set resolver",
            "nslookup api.bank.com\nnslookup -type=SRV _https._tcp.api.bank.com",
            "Non-authoritative vs authoritative answers in header. Timeout → firewall blocking UDP/53.",
            "Corporate VPN split-DNS: `nslookup` returned internal IP while public `dig @1.1.1.1` showed public—explained “works in office, fails from prod.”",
        ),
        (
            "resolvectl status",
            "**systemd-resolved** view—stub resolver, DNS servers per interface, routing domains.",
            "`status` — full picture\n`query HOST` — test resolution path\n`flush-caches` — after DNS cutover (careful)",
            "resolvectl status\nresolvectl query api.bank.com",
            "Look for **Link-specific DNS** vs global. **DNSSEC setting**. Misconfigured **~.` domain** routes all queries wrong.",
            "EKS node DNS flakes: **`127.0.0.53`** stub mis-forwarded to VPC resolver—`resolvectl status` showed stale upstream after DHCP renew.",
        ),
        (
            "ping",
            "**ICMP echo** reachability and RTT—not a substitute for TCP/443 health.",
            "- `-c N` — count\n- `-i SEC` — interval\n- `-s SIZE` — payload (MTU tests)\n- `-M do` — don't fragment\n- `-I iface` — source interface",
            "ping -c 5 10.0.1.1\nping -s 1472 -M do -c 3 gateway.bank.com",
            "**100% loss** → routing/firewall/ICMP blocked. **Frag needed** at size 1472 → **PMTU < 1500**. **Partial loss** → congestion or policer.",
            "“Host up but app down”: ping OK (ICMP allowed) but **:443 filtered**—explained to leadership why ping green ≠ service healthy.",
        ),
        (
            "traceroute",
            "Shows **forward path hops** via TTL expiry—UDP/ICMP depending on implementation.",
            "- `-n` numeric\n- `-T` TCP SYN (if supported)\n- `-I` ICMP echo",
            "traceroute -n 203.0.113.10\ntraceroute -T -p 443 api.bank.com",
            "Stars `* * *` mid-path may be **ICMP rate-limit**, not outage. Last hop missing → target firewall.",
            "Latency jump at hop 4 consistently—provider **hot potato** change; opened ticket with traceroute proof.",
        ),
        (
            "tcptraceroute",
            "Traces path using **TCP packets**—useful when ICMP blocked but **443/tcp** allowed.",
            "- `-p PORT` — destination port\n- `-n` numeric",
            "sudo tcptraceroute -n -p 443 api.bank.com",
            "Path follows **stateful firewalls** that permit established flows. Stalls after SYN without SYN-ACK → ACL drop.",
            "Partner “network open” claim disproved: **`tcptraceroute -p 443`** stopped at their edge; ICMP traceroute looked fine.",
        ),
        (
            "mtr -rwzbc 100",
            "**Combines ping + traceroute** with continuous statistics—best for intermittent loss/latency.",
            "- `-r` report mode\n- `-w` wide\n- `-z` show AS\n- `-b` show both host/IP\n- `-c 100` — 100 probes",
            "mtr -rwzbc 100 api.bank.com\nmtr -n -T -P 443 api.bank.com",
            "Watch **Loss%** per hop (beware **ICMP bias**). **Worst** and **Last** RTT columns for drift.",
            "Intermittent 2% payment failure: **`mtr`** showed 15% loss only on hop 6—provider fixed congested peering.",
        ),
        (
            "tcpdump",
            "**Packet capture** at the wire—ultimate ground truth for RST, retrans, TLS failures.",
            "- `-i eth0` — interface\n- `-nn` — no DNS/port names\n- `-vvv` — verbose\n- `-w file.pcap` — save\n- `-c N` — stop count\n- `-s0` — full snaplen",
            "sudo tcpdump -i any -nn -vvv host 10.0.5.20 and port 443 -w /tmp/capture.pcap\nsudo tcpdump -nn 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0'",
            "**SYN retrans** → no SYN-ACK. **RST** after SYN → ACL/port closed. **Zero-window** → receiver backlog. **TLS ClientHello without ServerHello** → middlebox or cipher mismatch.",
            "Vendor denied sending RST: **`tcpdump`** showed **`[R.]`** from their IP within 2ms of SYN—ticket closed in our favor; firewall rule fixed.",
        ),
        (
            "ip addr",
            "Shows **IP addresses** per interface—from **`iproute2`** suite (replaces `ifconfig`).",
            "`addr show` — all\n`addr show dev eth0` — one NIC",
            "ip -br addr\nip addr show dev eth0",
            "Missing **`UP`** flag → link down. **Secondary IPs** for VIP/keepalived. **scope link** vs **global**.",
            "Keepalived failover left **`eth0:1`** stale secondary—applications bound to wrong source IP; `ip addr` caught ghost VIP.",
        ),
        (
            "ip link",
            "**Layer-2 interface state**—up/down, MTU, promiscuous mode.",
            "`link show`\n`link set eth0 mtu 9000`",
            "ip -br link\nip link show eth0",
            "**MTU mismatch** causes black-hole TCP (small ping works, large transfers hang). **`state DOWN`** → cable/driver.",
            "Jumbo frames enabled on host but not switch—large S3 uploads hung; **`ip link`** MTU 9000 vs path 1500; PMTUD fix.",
        ),
        (
            "ip route",
            "**Routing table**—where packets go next.",
            "`route show`\n`route get DST` — resolved path for one destination",
            "ip route show table all\nip route get 203.0.113.55 from 10.0.1.5",
            "Wrong **default via** → asymmetric routing. **Policy routing** tables (`ip rule`) common in multi-NIC servers.",
            "Pod egress SNAT issue: **`ip route get`** from pod IP showed table **`100`** rule sending traffic to wrong gateway.",
        ),
        (
            "ip neigh",
            "**ARP/NDP neighbor cache**—L2 address for L3 next hop.",
            "`neigh show` — cache\n`neigh flush` — careful on prod",
            "ip neigh show\nip -s neigh show dev eth0",
            "**`STALE`/`REACHABLE`** normal. **`FAILED`** → ARP miss (wrong VLAN, host down). **Flapping REACHABLE** → loop/mac move.",
            "Mystery partial connectivity: **`ip neigh`** showed **`INCOMPLETE`** for default gateway—bad switch port security.",
        ),
        (
            "ethtool -S eth0",
            "**NIC hardware statistics**—drops, errors, ring overruns—not visible in `ifconfig` alone.",
            "- `-S` — stats\n- `-g` — ring parameters\n- `-k` — offload settings",
            "ethtool -S eth0 | egrep 'drop|err|miss'\nethtool -g eth0",
            "Rising **`rx_missed_errors`** or **`rx_fifo_errors`** → buffer overrun at line rate. **`tx_dropped`** → qdisc/backpressure.",
            "Payment spike: **`rx_missed_errors`** climbed with UDP syslog storm—moved logging off data NIC.",
        ),
        (
            "iptables -L -n -v",
            "**Netfilter rules** listing with counters—debug DNAT/SNAT/filter drops.",
            "- `-L` list\n- `-n` numeric\n- `-v` verbose counters\n- `-t nat` NAT table",
            "sudo iptables -L -n -v\nsudo iptables -t nat -L -n -v",
            "Non-zero **DROP/REJECT counters** climbing during incident → rule hit. Compare **`raw`/`mangle`/`filter`/`nat`** tables.",
            "“Random” API failures: **`iptables -L -n -v`** showed REJECT on NEW from pod CIDR after automation pushed wrong rule.",
        ),
        (
            "conntrack -L",
            "Inspect **connection tracking table**—critical when **`nf_conntrack: table full`** drops packets.",
            "- `-L` — list (heavy)\n- `-S` — stats\n- `-C` — count",
            "sudo conntrack -S\ngrep conntrack /proc/sys/net/netfilter/nf_conntrack_count",
            "Compare **count vs max**. High **TCP half-open** → SYN flood or scan. **Timeouts** too long → table churn slow.",
            "Peak UPI traffic: kernel dropped packets; **`conntrack -S`** at 99% of **`nf_conntrack_max`**. Raised max *and* reduced **`nf_conntrack_tcp_timeout_time_wait`** after modeling.",
        ),
        (
            "bpftrace / BCC tcpretrans",
            "**eBPF** programs attach kernel tracepoints/kprobes for low-overhead production signals—retransmits, syscall latency, run queue delay.",
            "**bpftrace:** `-e 'PROGRAM'` inline script; **`count()`**, **`hist()`** aggregations\n**BCC:** `/usr/share/bcc/tools/tcpretrans`, `biolatency`, `runqlat`",
            "sudo bpftrace -e 'tracepoint:tcp:tcp_retransmit { @[comm] = count(); }'\nsudo /usr/share/bcc/tools/tcpretrans 5\nsudo /usr/share/bcc/tools/runqlat 1 10",
            "Spikes in **`tcp_retransmit`** by **`comm`** pinpoint blame without packet capture. **`runqlat`** ms buckets explain tail latency when CPU looks idle (runnable queue).",
            "CRED-style p99 regression: **`tcpretrans`** implicated one downstream dependency IP; **`tcpdump`** confirmed vendor-side loss—avoided week-long app profiling rabbit hole.",
        ),
    ]

    parts.append("\n## Module 4: The SRE Network Diagnostic Toolkit\n\n")
    for c in commands_m4:
        parts.append(cmd(*c))

    parts.append(
        """
### Advanced: eBPF for SRE (brief)

| Tool | Use |
|------|-----|
| **`bpftrace`** | One-liners on tracepoints (`tcp_retransmit`, `runqlat`) |
| **`bcc`/`libbpf` tools** | `tcpretrans`, `execsnoop`, `biolatency` |
| **`perf`** | CPU flamegraphs + off-CPU stacks |

Example:

```bash
sudo bpftrace -e 'tracepoint:tcp:tcp_retransmit { @[comm] = count(); }'
sudo /usr/share/bcc/tools/tcpretrans 5
```

During outages, eBPF proves **where** time is spent without restarting apps with `strace` overhead.

---

## Module 5: Top 30 SRE Linux & Networking Interview Questions

"""
    )

    interviews = [
        (
            "1. Step-by-step: What happens when you type `curl https://api.bank.com/v1/pay`?",
            """**Answer (senior bar):**
1. **Shell** parses command; **curl** loads CA bundle, resolves **`api.bank.com`** via glibc NSS → **`/etc/resolv.conf`** / stub resolver → recursive resolver → authoritative A/AAAA (possibly CNAME chain).
2. **Routing:** Kernel **`FIB`** picks egress iface/gateway; **ARP/`ip neigh`** resolves next-hop MAC.
3. **Socket:** `socket()` → `connect()` triggers **TCP SYN** to :443 (or Happy Eyeballs if IPv6/IPv4).
4. **Handshake:** SYN → SYN-ACK → ACK; **congestion window** starts (slow start).
5. **TLS 1.3:** ClientHello → ServerHello → encrypted cert verify → Finished; **SNI** selects cert; **ALPN** negotiates HTTP/1.1 or h2.
6. **HTTP:** `GET/POST` over TLS record layer; server **accept queue** already consumed at listen socket during handshake burst.
7. **Response path:** NIC → TCP reassembly → TLS decrypt → curl **`write()`** to stdout; metrics show latency as DNS + TCP + TLS + TTFB + download.
8. **Failure hooks:** DNS TTL staleness, SYN drop (LB), **`CLOSE_WAIT`** leak, cert expiry, MTU black hole, **HTTP 502** from upstream not TCP failure.""",
        ),
        (
            "2. Load average vs CPU utilization—load 10 on 4 cores with 10% CPU?",
            """**Yes, possible.** Load average includes **runnable + uninterruptible (`D`)** threads. Example: 40 threads stuck in **`D`** on NFS + 0.4 runnable cores ≈ load ~10 with **~10% CPU busy**. Always triage with **`top`/`ps` STAT**, **`iostat`**, **`mount`** stats—not CPU alone.""",
        ),
        (
            "3. `No space left on device` but `df -h` shows 45% used?",
            """**Causes:** (1) **inode exhaustion** (`df -i` 100%), (2) **quota**, (3) **unlinked open files** (`lsof +L1`), (4) **wrong filesystem** (full `/var` while checking `/`). **Fix:** delete files / rotate logs / restart holder / expand inodes (recreate fs) / fix quota.""",
        ),
        (
            "4. `TIME_WAIT` vs `CLOSE_WAIT`; 10,000 `CLOSE_WAIT`?",
            """**TIME_WAIT:** Local side closed first; waits **2×MSL** for stray segments—normal on high-churn **clients**. **CLOSE_WAIT:** Remote sent **FIN**; **application never `close()`**—**app bug/leak**, not kernel/network. **10k CLOSE_WAIT** → restart mitigates; fix code + FD limits + connection pool lifecycle.""",
        ),
        (
            "5. `ping` vs `traceroute`; ping OK but :443 hangs?",
            """**Ping** tests **ICMP** reachability. **Traceroute** maps **path** (TTL). **Port 443** needs **TCP connect** + TLS + app. ICMP allowed + **TCP drop/filter** → ping success, curl hang. Use **`tcptraceroute -p 443`**, **`nc -vz`**, **`curl -v`**, **`tcpdump`**.""",
        ),
        (
            "6. Intermittent 5s connection timeouts at peak—isolate DNS vs SYN vs conntrack vs thread pool?",
            """**Method:**
1. Timestamp correlate **metrics** (p99 connect latency).
2. **`dig +stats`** latency vs **`/etc/resolv.conf`**.
3. **`ss -s`**, **`tcpdump`** SYN retrans count, **`conntrack -S`** fullness.
4. **`strace -e trace=network -T`** on app—where 5s spent?
5. **Thread pool** → app logs + **`jstack`**/profiler if connect is fast but request slow.
6. **Firewall** → **`iptables -L -n -v`**, **`nf_conntrack`** drops in **`journalctl -k`**.""",
        ),
        (
            "7. User vs kernel space; duplicate process vs new program?",
            """**User space** (Ring 3) apps; **kernel space** (Ring 0) privileged. **Syscalls** bridge them. **`fork()`** duplicates process; **`execve()`** loads new program image. **`clone()`** fine-grained (threads).""",
        ),
        (
            "8. OOM Killer selection and protecting kubelet/sshd?",
            """OOM uses **`oom_score`** heuristics (memory usage, runtime, root, child processes). Tune **`/proc/PID/oom_score_adj`** (-1000 prevents kill for critical daemons on some policies). **Kubernetes:** QoS **Guaranteed**, **`memory limits`**, **`system-reserved`**, **`kube-reserved`**, **`oom_score_adj`** in kubelet config. **sshd:** **`OOMScoreAdjust=-1000`** in systemd unit.""",
        ),
        (
            "9. When `ss` over `netstat`; inspect listen backlog?",
            """**`ss`** reads stats from **`/proc/net/*`** efficiently. **`ss -ltn`** shows **Recv-Q/Send-Q**; for listeners **Recv-Q** = completed connections waiting for **`accept()`**. Compare to **`somaxconn`** and app backlog.""",
        ),
        (
            "10. tcpdump proving vendor sends TCP RST?",
            """Capture on client/host: **`tcpdump -i any -nn host VENDOR_IP and port 443 -w proof.pcap`**. Show **`[S]`** then **`[R.]`** from **vendor IP** with no **`[S.]`** completion—or **RST after data**. Share **pcap** + **frame numbers**; correlate with **UTC NTP-synced** time.""",
        ),
        (
            "11. Explain `SYN backlog` vs `accept queue`.",
            "**SYN backlog** (`tcp_max_syn_backlog`) holds half-open connections during handshake. **Accept queue** (`min(backlog, somaxconn)`) holds fully established sockets until **`accept()`**. Drops manifest as **client SYN retrans** while CPU is idle.",
        ),
        (
            "12. What is head-of-line blocking in HTTP/1.1 vs HTTP/2?",
            "HTTP/1.1: one slow response blocks connection reuse. HTTP/2 multiplexes streams on one TCP connection—still subject to **TCP HOL** on loss. HTTP/3 over QUIC solves transport HOL for web workloads.",
        ),
        (
            "13. How does PMTUD black hole happen?",
            "ICMP **Fragmentation Needed** blocked while DF set → TCP sends full MSS forever with no progress. Fix: lower **MSS clamp** (`iptables -t mangle -TCPMSS`), enable ICMP, or reduce interface MTU consistently.",
        ),
        (
            "14. Difference between softirq and process CPU?",
            "Network RX can burn **softirq** on ksoftirqd CPUs showing high **`%hi`** in `mpstat` while app CPU looks fine—check **`/proc/softnet_stat`**, RPS/RFS, NIC offload.",
        ),
        (
            "15. When is `tcp_tw_reuse` safe?",
            "Modern kernels changed semantics; **do not tune by blog posts**. Measure **`TIME_WAIT`** counts, connection churn, and ephemeral port usage first. Prefer **more local ports**, **connection pooling**, **proper LB** over aggressive reuse.",
        ),
        (
            "16. Explain `SO_REUSEPORT`.",
            "Multiple binders share load at **hash of 4-tuple**—reduces accept skew on multi-core. Misconfig can cause uneven workers (`htop` skew).",
        ),
        (
            "17. How do cgroups v2 limit memory and affect OOM?",
            "**memory.max** triggers cgroup OOM killer before host OOM; pods die independently. SRE must set **requests/limits** and watch **memory.high** throttling.",
        ),
        (
            "18. Debug `Certificate verify failed` in production safely.",
            "Compare **SNI**, **intermediate chain**, **clock skew**, **corporate MITM proxy**. Use **`openssl s_client -connect host:443 -servername host -showcerts`** from **same network namespace** as app.",
        ),
        (
            "19. What does `nf_tables` vs `iptables` mean for ops?",
            "nftables backend on modern distros; **`iptables-nft`** translates rules. Counters and rule paths differ—validate automation targets correct backend.",
        ),
        (
            "20. How to prove asymmetric routing?",
            "`tcpdump` on both directions, **`ip route get`**, **`conntrack`** entries. SYN arrives iface A, return via B → stateful firewall may drop.",
        ),
        (
            "21. Role of `systemd` socket activation?",
            "Service starts on first connect—impacts **listen backlog** timing and FD inheritance; know **`Accept=yes`** units for superservers.",
        ),
        (
            "22. Explain `epoll` vs `select` for SRE.",
            "High-connection APIs use **epoll** edge/level triggered. **Thousands of idle connections** → watch **FD ulimit** and **epoll_wait** latency under load.",
        ),
        (
            "23. What is TCP keepalive vs HTTP keep-alive?",
            "TCP keepalive detects dead peers at L4; HTTP keep-alive reuses TCP for multiple requests—different timeouts; misaligned idle timeouts cause **RST surprises**.",
        ),
        (
            "24. How do you read `ss -i` TCP info?",
            "Fields like **rtt**, **cwnd**, **retrans**—rising **retrans** with stable RTT suggests loss; RTT spike without retrans suggests bufferbloat/path change.",
        ),
        (
            "25. Diagnose DNS latency vs application latency.",
            " **`dig +stats`** for Query time; app metrics with **`trace DNS`** span; if DNS 2ms but p99 500ms, look TCP/TLS/backend.",
        ),
        (
            "26. Safe production use of `strace`.",
            "Attach briefly; **`-c`** summary mode; filter **`-e trace=`**; detach—heavy strace slows apps; prefer **eBPF** for long captures.",
        ),
        (
            "27. What triggers zombie processes?",
            "Child exited, parent didn't **`wait()`**. Fix parent bug; zombies don't use memory but consume PIDs if unbounded.",
        ),
        (
            "28. Explain VFS and page cache for log-heavy apps.",
            "Writes go to **page cache** marked dirty; **`pdflush`** flushes. Burst logging → **high dirty ratio**, **`iowait`**, latency— tune **`/proc/sys/vm/dirty_*`** or reduce sync logging.",
        ),
        (
            "29. Kubernetes networking: where do drops happen?",
            "CNI overlay, **iptables/IPVS**, **kube-proxy**, **NetworkPolicy**, node **conntrack**, **CoreDNS**—isolate with **`tcpdump -i any`** in pod netns and **`ss`** on node.",
        ),
        (
            "30. Design an on-call runbook for total payment API outage (first 15 minutes).",
            "1) Confirm blast radius & SLO burn 2) Check recent deploys/feature flags 3) **`ss -s`/`conntrack`** 4) **DNS/TLS/LB** health 5) **DB/Redis** dependencies 6) **`tcpdump`/vendor status** 7) comms + rollback decision 8) post-incident **blameless** timeline with evidence artifacts.",
        ),
    ]

    for q, a in interviews:
        parts.append(f"### {q}\n\n{a}\n\n")

    parts.append(
        """
## Module 6: Step-by-Step 14-Day Hands-On Study & Terminal Practice Plan

| Day | Theory (read) | Terminal drills (do) | Success criteria |
|-----|---------------|----------------------|------------------|
| **1** | Module 1: rings, syscalls, `/proc` | `nproc`, read `/proc/cpuinfo`, `/proc/meminfo`, `/proc/sys/kernel/pid_max` | Explain Ring 0 vs 3 to a peer in 2 minutes |
| **2** | Process states, fork/exec | Spawn `sleep 300 &`, `ps`, `kill -STOP`, observe `T` state | Identify `D` vs `S` in `ps` man page |
| **3** | FDs, ulimits | `ulimit -n`, open many files script until error, fix with `LimitNOFILE` | Reproduce & fix **EMFILE** locally |
| **4** | Module 2 CPU | `mpstat -P ALL 1`, `pidstat -u 1`, stress-ng CPU | Correlate load vs CPU on stressed host |
| **5** | Memory & OOM | `free -w`, `vmstat 1`, tune `oom_score_adj` on test process | Predict OOM victim with `/proc/PID/oom_score` |
| **6** | Disk & inodes | Create many small files to exhaust inodes; fix with `df -i` | Recover without reboot |
| **7** | `strace`/`lsof` | Trace `curl` connect; find `+L1` deleted log scenario | Capture 5s connect delay in strace log |
| **8** | Module 3 TCP/DNS | Draw handshake; `dig +trace` on real domain | List socket states from `/proc/net/tcp` |
| **9** | `ss`/`tcpdump` localhost | Run `nc -l 9999`, connect, capture SYN/FIN | Explain Recv-Q on listener |
| **10** | Path MTU | `ping -s 1472 -M do` to external host | Detect PMTU issue or confirm end-to-end 1500 |
| **11** | `mtr`/`tcptraceroute` | Compare ICMP vs TCP path to :443 | Document hop with highest loss |
| **12** | Conntrack lab | Fill table in sandbox; observe kernel log message | Mitigate with sysctl + timeout tuning |
| **13** | systemd/journal | Break unit intentionally; restore with `journalctl -u` | Write 5-line postmortem from logs alone |
| **14** | Mock incident | Combine: DNS wrong + SYN drop script; triage in 30 min | Produce pcap + 1-page RCA |

### Sandbox setup (safe local practice)

```bash
# Network namespace lab (no root cloud needed on laptop)
sudo ip netns add sre-lab
sudo ip link add veth0 type veth peer name veth1
sudo ip link set veth1 netns sre-lab
# ... assign IPs, run tcpdump on veth0, curl from netns
```

### Daily habit (30 min maintenance)

- One **`tcpdump`** exercise, one **`ss -s`** snapshot on a real server (read-only), one **`dig +trace`** for a dependency you own.

---

## Appendix A: TCP state quick reference

| Hex (`/proc/net/tcp`) | State |
|-----------------------|-------|
| 01 | ESTABLISHED |
| 02 | SYN_SENT |
| 03 | SYN_RECV |
| 04 | FIN_WAIT1 |
| 05 | FIN_WAIT2 |
| 06 | TIME_WAIT |
| 07 | CLOSE |
| 08 | CLOSE_WAIT |
| 0A | LISTEN |

## Appendix B: Recommended reading

- *Site Reliability Engineering* (Google) — Ch. 6 Monitoring, Ch. 28 Accelerating SREs
- *Systems Performance* (Gregg) — CPU, memory, network chapters
- *TCP/IP Illustrated, Volume 1* (Stevens) — protocol ground truth
- Linux man pages: `socket(7)`, `tcp(7)`, `ip(7)`, `systemd.system(5)

---

*Document version 1.0 — generated for production SRE interview and on-call preparation.*
"""
    )

    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
