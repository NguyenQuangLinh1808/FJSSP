from collections import defaultdict


def apply_c7_new(solver):
    # Constraint 8: Tránh xung đột (Overlap)
    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, _ in solver.ops[i]['machines']:
            mach_to_ops[m].append(i)

    shared_machines = defaultdict(list)
    for mach in sorted(mach_to_ops.keys()):
        ops = mach_to_ops[mach]
        n_ops = len(ops)
        for idx1 in range(n_ops):
            for idx2 in range(idx1 + 1, n_ops):
                i, j = ops[idx1], ops[idx2]
                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']: continue
                pair = (i, j) if i < j else (j, i)
                shared_machines[pair].append(mach)

    for (i, j) in sorted(shared_machines.keys()):
        machines = shared_machines[(i, j)]
        sm_var = solver.get_var('SM', i, j)

        # 8a Mới: M_{i,a} & M_{j,a'} -> ~SM_{i,j} với mọi a khác a'
        for m_i, _ in solver.ops[i]['machines']:
            for m_j, _ in solver.ops[j]['machines']:
                if m_i != m_j:
                    solver.add_clause_smart([
                        -solver.get_var('M', i, m_i),
                        -solver.get_var('M', j, m_j),
                        -sm_var
                    ])

        # 8a: M_{i,m} & M_{j,m} -> SM_{i,j}
        for mach in machines:
            solver.add_clause_smart([-solver.get_var('M', i, mach), -solver.get_var('M', j, mach), sm_var])

        # 8b: SM_{i,j} -> ~(A_{i,t} & A_{j,t})
        start_chk = max(solver.est[i], solver.est[j])
        max_p_i = max(p for m, p in solver.ops[i]['machines'] if m in machines)
        max_p_j = max(p for m, p in solver.ops[j]['machines'] if m in machines)
        end_chk = min(solver.horizon, solver.lst[i] + max_p_i, solver.lst[j] + max_p_j)

        if start_chk >= end_chk: continue

        for t in range(start_chk, end_chk + 1):
            a_i = solver.var_map.get(('A', i, t))
            a_j = solver.var_map.get(('A', j, t))
            if a_i is not None and a_j is not None:
                solver.add_clause_smart([-sm_var, -a_i, -a_j])
