def get_heuristic_bound(jobs, num_machines):
    num_jobs = len(jobs)
    current_op_idx = [0] * num_jobs
    job_avail = [0] * num_jobs
    machine_avail = [0] * num_machines
    total_ops = sum(len(job) for job in jobs)
    ops_scheduled = 0

    while ops_scheduled < total_ops:
        best_job = -1
        best_mach = -1
        best_completion = float('inf')

        for j in range(num_jobs):
            if current_op_idx[j] < len(jobs[j]):
                o_idx = current_op_idx[j]
                for mach, p in jobs[j][o_idx]:
                    start_time = max(job_avail[j], machine_avail[mach])
                    completion_time = start_time + p
                    if completion_time < best_completion:
                        best_completion = completion_time
                        best_job = j
                        best_mach = mach

        job_avail[best_job] = best_completion
        machine_avail[best_mach] = best_completion
        current_op_idx[best_job] += 1
        ops_scheduled += 1

    return max(machine_avail)

def validate_solution(jobs, schedule):
    if not schedule: return False, "Lịch trình rỗng"

    total_ops = sum(len(job) for job in jobs)
    if len(schedule) != total_ops: return False, f"Missing Ops: {len(schedule)}/{total_ops}"

    sch_map = {(x['job_idx'], x['op_idx']): x for x in schedule}
    mach_use = {}

    for x in schedule:
        j_idx, o_idx, m, s, e = x['job_idx'], x['op_idx'], x['machine'], x['start'], x['end']

        if e <= s:
            return False, f"Lỗi logic thời gian Job {j_idx} Op {o_idx}: start={s}, end={e}"

        valid_machines = dict(jobs[j_idx][o_idx])
        if m not in valid_machines:
            return False, f"Máy {m} không được phép xử lý Job {j_idx} Op {o_idx}"

        expected_duration = valid_machines[m]
        if e - s != expected_duration:
            return False, f"Sai thời gian gia công: kỳ vọng {expected_duration}, thực tế {e - s}"

        if o_idx > 0:
            prev = sch_map.get((j_idx, o_idx - 1))
            if not prev or prev['end'] > s:
                return False, f"Lỗi Precedence: Job {j_idx} Op {o_idx} bắt đầu sớm"

        if m not in mach_use: mach_use[m] = []
        mach_use[m].append(x)

    for m, items in mach_use.items():
        items.sort(key=lambda k: k['start'])
        for k in range(len(items) - 1):
            if items[k]['end'] > items[k + 1]['start']:
                return False, f"Lỗi Overlap trên Máy {m}"

    return True, max(x['end'] for x in schedule)