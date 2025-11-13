## Check Real Time Kernel




sudo pro status

ensure real time kernel is enabled


grep PREEMPT /boot/config-$(uname -r)

Expected
CONFIG_PREEMPT_RT=y



uname -r

expected
6.8.1-1036-realtime



sudo apt install rt-tests
sudo cyclictest -t1 -p80  -i1000 -l10000

Breakdown:

policy: fifo → the thread is running with SCHED_FIFO (hard real-time policy). ✅

T: 0 → thread ID 0 (your only test thread).

P:80 → real-time priority 80 (high, good).

I:1000 → interval = 1000 µs → 1 kHz wakeup rate.

C:10000 → it ran 10,000 cycles.

Min: 2 → best latency = 2 µs

Avg: 4 → average latency = 4 µs

Max: 35 → worst latency = 35 µs

For a PREEMPT_RT kernel, especially on a general-purpose desktop/laptop with stuff running in the background, a max jitter of 35 µs is solid. That absolutely confirms:

✅ Your RT kernel is working and giving you deterministic, low-latency scheduling.


----

But honestly, with:

Max: 35 µs

You’re already in a very healthy RT range.
If you tell me what loop rate you’re targeting for your robot/control app (e.g. 1 kHz control loop, 250 µs step, etc.), I can help you translate these numbers into “safe / not safe” specifically for your use case.


-----

sudo cyclictest -t2 -a2,3 -p80 -m -i1000 -l200000 -v


Expected


       0:    5273:       3
       0:    5274:       2
       0:    5275:       2
       0:    5276:       2
       1:    3511:       2
       1:    3512:       3
       1:    3513:       4
       1:    3514:       7
       1:    3515:       2
       1:    3516:       2
       1:    3517:       2

--------



Trial

sudo sysctl -w kernel.sched_rt_runtime_us=-1

# 2) stop irqbalance temporarily
sudo systemctl stop irqbalance

# 3) run 2-thread cyclictest on 2 cores, 1kHz
sudo cyclictest \
  -t2 \          # 2 threads
  -a2,3 \        # pin threads to CPU 2 and 3
  -p80 \         # RT prio 80
  -m \           # mlockall()
  -i1000 \       # 1000 µs period (1kHz)
  -l200000 \     # more cycles
  -v
----


# /dev/cpu_dma_latency set to 0us
policy: other/other: loadavg: 3.71 4.06 3.51 1/1819 858177

T: 0 (858133) P: 0 I:1000 C:   8876 Min:     12 Act:   56 Avg:   59 Max:    2199
T: 1 (858134) P: 0 I:1500 C:   5918 Min:      8 Act:   57 Avg:   60 Max:    1361


What this really means

policy: other/other → both threads are running with SCHED_OTHER, the normal Linux time-sharing policy, not real-time.

P: 0 → both threads have priority 0 (non-RT).

So this test is measuring “normal desktop Linux”, not your RT scheduler.

That’s why:

Max latencies are 362 µs and 130 µs.

The numbers are actually not terrible, but they’re not showing your RT kernel ability — we want to see SCHED_FIFO here.

You probably:

Ran cyclictest without sudo, or

Used -p80 but cyclictest failed to set RT priority and silently fell back to other (often prints a warning you might have missed).

-----

Expected

policy: fifo/fifo: ...
T: 0 (...) P:80 I:1000 ... Max: XX
T: 1 (...) P:80 I:1500 ... Max: YY

-------

echo "Max jitter:" $(grep -E ":\s*[0-9]+:" cyclictest-rt.txt | awk '{print $2}' | sort -n | tail -1)
echo ">1ms count:" $(grep -E ":\s*[1-9][0-9]{3}:" cyclictest-rt.txt | awk '{sum+=$3} END{print sum+0}')
