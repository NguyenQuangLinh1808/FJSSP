# constraints_ver2/mvcc.py
from collections import defaultdict
from itertools import combinations

def apply_mvcc(solver):
    """
    M-Variable Cumulative Capacity (MVCC) Preprocessing.
    Fire ngay khi 3 biến M được quyết định trên cùng một máy.
    Dựa trên nguyên lý Energetic: nếu 3 Ops không thể nhét vừa
    trong bất kỳ window [α, β] nào trên máy m -> Cấm tổ hợp M này.
    """
    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            mach_to_ops[m].append((i, p))

    for mach, ops_on_m in mach_to_ops.items():
        if len(ops_on_m) < 3:
            continue

        # Tạo tất cả các Event-based windows [α, β]
        alphas = sorted({solver.est[i]           for i, _ in ops_on_m})
        betas  = sorted({solver.lst[i] + p - 1   for i, p in ops_on_m})
        windows = [(α, β) for α in alphas for β in betas if β >= α]

        for (α, β) in windows:
            capacity = β - α + 1

            # Tính energy contribution (diện tích bắt buộc) của từng op
            contrib = []
            for (i, p_im) in ops_on_m:
                e = max(0, min(p_im,
                               min(solver.lst[i] + p_im, β + 1) - max(solver.est[i], α)))
                if e > 0:
                    contrib.append((i, e))

            if len(contrib) < 3:
                continue

            # Kiểm tra mọi triples có thể (O(n^3) - n là số ops/máy)
            for (i, ei), (j, ej), (k, ek) in combinations(contrib, 3):
                # Bỏ qua nếu có 2 job giống nhau (ràng buộc C4 đã xử lý logic job)
                if (solver.ops[i]['job_idx'] == solver.ops[j]['job_idx'] or
                    solver.ops[i]['job_idx'] == solver.ops[k]['job_idx'] or
                    solver.ops[j]['job_idx'] == solver.ops[k]['job_idx']):
                    continue

                # Cắt ngay lập tức nếu tổng năng lượng tràn dung lượng máy
                if ei + ej + ek > capacity:
                    solver.add_clause_smart([
                        -solver.get_var('M', i, mach),
                        -solver.get_var('M', j, mach),
                        -solver.get_var('M', k, mach)
                    ])

def update_mvcc_incremental(solver, new_limit):
    """
    Kích hoạt liên tục trong quá trình Incremental Solving.
    Khi upper bound makespan giảm, capacity của window [0, new_limit] giảm,
    tạo ra những cụm 3 biến M bị xung đột mới.
    """
    if not hasattr(solver, '_mvcc_excl_triples'):
        solver._mvcc_excl_triples = set()

    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            mach_to_ops[m].append((i, p))

    α, β = 0, new_limit
    capacity = new_limit + 1

    for mach, ops_on_m in mach_to_ops.items():
        contrib = []
        for (i, p_im) in ops_on_m:
            e = max(0, min(p_im,
                           min(solver.lst[i] + p_im, β + 1) - max(solver.est[i], α)))
            if e > 0:
                contrib.append((i, p_im, e))

        # Quét lại triples với capacity mới
        for (i, _, ei), (j, _, ej), (k, _, ek) in combinations(contrib, 3):
            if (solver.ops[i]['job_idx'] == solver.ops[j]['job_idx'] or
                solver.ops[i]['job_idx'] == solver.ops[k]['job_idx'] or
                solver.ops[j]['job_idx'] == solver.ops[k]['job_idx']):
                continue

            # Đảm bảo không ném lại clause đã từng thêm trước đó
            key = tuple(sorted([i, j, k]) + [mach])
            if key in solver._mvcc_excl_triples:
                continue

            # Nếu tràn -> Cắt
            if ei + ej + ek > capacity:
                solver.add_clause_smart([
                    -solver.get_var('M', i, mach),
                    -solver.get_var('M', j, mach),
                    -solver.get_var('M', k, mach)
                ])
                solver._mvcc_excl_triples.add(key)