# Sourced by the Control and Core start scripts. Both steps are optional and
# are requested through the environment, so Docker Compose (which pins CPUs and
# orders services itself) and Kubernetes run the same start script.

# Print one CPU number per line for a list such as "0-5,7-13,15".
expand_cpu_list() {
  local list="${1//[[:space:]]/}" part first last cpu
  local -a parts cpus=()
  [[ "${list}" =~ ^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$ ]] || return 1
  IFS=, read -r -a parts <<< "${list}"
  for part in "${parts[@]}"; do
    first="${part%-*}" last="${part#*-}"
    (( 10#${first} <= 10#${last} )) || return 1
    for (( cpu = 10#${first}; cpu <= 10#${last}; cpu++ )); do cpus+=("${cpu}"); done
  done
  printf '%s\n' "${cpus[@]}" | sort -n -u
}

# Restrict this shell (and everything it starts) to exactly the given CPUs.
# The kernel silently drops CPUs the container may not use, so read the
# result back and fail when it differs from the request.
pin_to_cpus() {
  local requested allowed
  requested="$(expand_cpu_list "$1")" || { echo "Invalid CPU list: '$1'." >&2; return 1; }
  taskset --cpu-list --pid "$1" "$$" > /dev/null \
    || { echo "Cannot pin to CPUs $1." >&2; return 1; }
  allowed="$(expand_cpu_list "$(taskset --cpu-list --pid "$$" | sed 's/.*: *//')")"
  if [[ "${requested}" != "${allowed}" ]]; then
    echo "Requested CPUs $1, allowed $(tr '\n' ' ' <<< "${allowed}"). Check the node topology and the container's CPU allocation." >&2
    return 1
  fi
}

# wait_for_ports SECONDS PORT... : wait until every localhost TCP port accepts
# a connection. SECONDS=0 skips the wait.
wait_for_ports() {
  local seconds="$1" port deadline
  shift
  [[ "${seconds}" =~ ^[0-9]+$ ]] || { echo "Start-up wait must be a whole number of seconds." >&2; return 1; }
  (( seconds > 0 )) || return 0
  echo "Waiting up to ${seconds} s for localhost ports $*..."
  deadline=$((SECONDS + seconds))
  for port in "$@"; do
    until (exec 3<> "/dev/tcp/127.0.0.1/${port}") 2> /dev/null; do
      if (( SECONDS >= deadline )); then
        echo "Dependency on localhost port ${port} is unavailable." >&2
        return 1
      fi
      sleep 2
    done
  done
}
