from collections import defaultdict

def apply_energetic_pair_exclusion(solver):
    """
    Tiền xử lý tầng 2: Cấm cặp (Pair Exclusion).
    Nếu tải bắt buộc (Mandatory) + 2 tùy chọn (Optional) > Horizon
    -> 2 tùy chọn đó không thể cùng nằm trên máy m.
    """
    mandatory_load = [0] * solver.num_machines
    mandatory_set  = set()

    for i in range(solver.num_ops):
        # Lấy các máy còn sống
        viable = [(m, p) for m, p in solver.ops[i]['machines'] if (i, m) not in getattr(solver, 'killed_machines', set())]
        if len(viable) == 1:
            m, p = viable[0]
            mandatory_load[m] += p
            mandatory_set.add(i)

    mach_to_opt = defaultdict(list)
    for i in range(solver.num_ops):
        if i in mandatory_set:
            continue
        for m, p in solver.ops[i]['machines']:
            if (i, m) not in getattr(solver, 'killed_machines', set()):
                mach_to_opt[m].append((i, p))

    for mach, opt_ops in mach_to_opt.items():
        ml = mandatory_load[mach]
        n  = len(opt_ops)

        for a in range(n):
            for b in range(a + 1, n):
                i, p_i = opt_ops[a]
                j, p_j = opt_ops[b]

                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue

                if ml + p_i + p_j > solver.horizon:
                    m_var_i = solver.get_var('M', i, mach)
                    m_var_j = solver.get_var('M', j, mach)
                    solver.add_clause_smart([-m_var_i, -m_var_j])