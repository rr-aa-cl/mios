#!/usr/bin/env bash
# Pin every interrupt belonging to the network interface used for the Franka
# robot to the CPU reserved for the ROS 2 FCI container.  This script is safe
# to run repeatedly and deliberately discovers the route/IRQ at runtime: PCI
# MSI interrupt numbers are not stable across host reboots.
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root (for example: sudo $0)." >&2
  exit 1
fi

robot_ip=${ROBOT_IP:-192.168.4.100}
control_cpu=${MIOS_CONTROL_CPU:-6}
irq_priority=${MIOS_FRANKA_IRQ_PRIORITY:-90}

if ! [[ ${control_cpu} =~ ^[0-9]+$ ]]; then
  echo "MIOS_CONTROL_CPU must be one CPU number; received '${control_cpu}'." >&2
  exit 1
fi

if ! [[ ${irq_priority} =~ ^[1-9][0-9]?$ ]] || (( irq_priority > 99 )); then
  echo "MIOS_FRANKA_IRQ_PRIORITY must be an integer from 1 to 99; received '${irq_priority}'." >&2
  exit 1
fi

route=$(ip route get "${robot_ip}")
if ! interface=$(awk -v target="${robot_ip}" '
  {
    for (field = 1; field <= NF; ++field) {
      if ($field == "via") gateway = 1
      if ($1 == target && $field == "dev" && field < NF) {
        interface = $(field + 1)
      }
    }
  }
  END {
    if (gateway || interface == "" || interface == "lo") exit 1
    print interface
  }
' <<< "${route}"); then
  echo "Franka robot ${robot_ip} requires a direct, non-loopback route without a gateway." >&2
  exit 1
fi

discover_irqs() {
  local irq_path irq affinity_file
  local msi_irq_dir="/sys/class/net/${interface}/device/msi_irqs"
  # The PCI device lists all MSI/MSI-X vectors, including multiqueue handlers
  # whose interrupt action names have suffixes such as enp3s0-TxRx-0.
  irq_numbers=()
  if [[ -d ${msi_irq_dir} ]]; then
    for irq_path in "${msi_irq_dir}"/*; do
      irq=${irq_path##*/}
      if [[ ${irq} =~ ^[0-9]+$ ]]; then
        irq_numbers+=("${irq}")
      fi
    done
  fi

  # Older devices may not expose msi_irqs. Match action names literally so
  # similarly named interfaces and regex characters cannot select another NIC.
  if (( ${#irq_numbers[@]} == 0 )); then
    mapfile -t irq_numbers < <(awk -v interface="${interface}" '
      {
        irq = $1
        sub(":$", "", irq)
        if (irq !~ /^[0-9]+$/) next
        for (field = 2; field <= NF; ++field) {
          count = split($field, actions, ",")
          for (action = 1; action <= count; ++action) {
            if (actions[action] == interface || index(actions[action], interface "-") == 1) {
              print irq
            }
          }
        }
      }
    ' /proc/interrupts)
  fi

  if (( ${#irq_numbers[@]} == 0 )); then
    echo "No IRQs found for Franka interface ${interface}." >&2
    return 1
  fi

  mapfile -t irq_numbers < <(printf '%s\n' "${irq_numbers[@]}" | sort -nu)

  for irq in "${irq_numbers[@]}"; do
    affinity_file="/proc/irq/${irq}/smp_affinity_list"
    if [[ ! -w ${affinity_file} ]]; then
      echo "Cannot write ${affinity_file}." >&2
      return 1
    fi
  done
}

# Check every target before changing NIC settings or any IRQ affinity.
discover_irqs

# The Franka link is dedicated to the 1 kHz FCI transport.  Energy-efficient
# Ethernet, pause frames, and receive interrupt coalescing all trade latency
# for power or throughput, so disable them before the FCI container starts.
ethtool --set-eee "${interface}" eee off
ethtool --pause "${interface}" autoneg off rx off tx off
ethtool --coalesce "${interface}" rx-usecs 0
printf 'Disabled EEE, pause frames, and RX interrupt coalescing on %s.\n' "${interface}"

# A driver may reallocate IRQs when link settings change. Use the device's
# current vectors and check them again before writing any affinity.
discover_irqs

for irq in "${irq_numbers[@]}"; do
  affinity_file="/proc/irq/${irq}/smp_affinity_list"
  printf '%s\n' "${control_cpu}" > "${affinity_file}"
  printf 'Pinned IRQ %s (%s) to CPU %s.\n' "${irq}" "${interface}" "${control_cpu}"

  # The FCI transport cannot tolerate its network interrupt being delayed by
  # the controller-manager update loop.  Keep its threaded IRQ above the
  # controller's FIFO-80 thread on the dedicated CPU.
  # Linux truncates comm names, so only the numeric IRQ prefix is stable.
  mapfile -t irq_threads < <(ps -eLo tid=,comm= | awk -v prefix="irq/${irq}-" '
    index($2, prefix) == 1 && $1 ~ /^[0-9]+$/ && !seen[$1]++ { print $1 }
  ')
  if (( ${#irq_threads[@]} == 0 )); then
    echo "Warning: could not find threaded IRQ handler irq/${irq}-* (${interface})." >&2
    continue
  fi
  for thread_id in "${irq_threads[@]}"; do
    chrt --fifo --pid "${irq_priority}" "${thread_id}"
    printf 'Set IRQ thread %s to SCHED_FIFO priority %s.\n' "${thread_id}" "${irq_priority}"
  done
done
