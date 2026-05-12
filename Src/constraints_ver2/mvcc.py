import itertools
from collections import defaultdict


def apply_mvcc(solver, dynamic_lst=None):
    """
    M-Variable Cumulative Capacity (MVCC):
    Tìm các window [alpha, beta] mà năng lượng bắt buộc của một tập hợp
    operations (size <= 4) vượt quá sức chứa. Chém đứt nhánh bằng mệnh đề thuần M.
    """
    lst_array = dynamic_lst if dynamic_lst else solver.lst

    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            if (i, m) not in getattr(solver, 'killed_machines', set()):
                mach_to_ops[m].append((i, p))

    for mach, ops_on_m in mach_to_ops.items():
        # Xây dựng Event points
        alphas = set(solver.est[i] for i, _ in ops_on_m)
        betas = set(lst_array[i] + p - 1 for i, p in ops_on_m)

        for alpha in alphas:
            for beta in betas:
                if alpha > beta: continue
                window_size = beta - alpha + 1

                # Tính mandatory energy e_i cho từng op
                energies = []
                for i, p in ops_on_m:
                    # Công thức Left/Right Shift Overlap chuẩn xác
                    space_before = max(0, alpha - solver.est[i])
                    space_after = max(0, lst_array[i] + p - 1 - beta)
                    e = max(0, p - space_before - space_after)

                    if e > 0:
                        energies.append((i, e))

                if not energies: continue

                # Chỉ check các tập con kích thước từ 2 đến 4 (quá đủ để tạo conflict ngắn)
                for k in range(2, min(5, len(energies) + 1)):
                    for subset in itertools.combinations(energies, k):
                        sum_e = sum(e for _, e in subset)
                        if sum_e > window_size:
                            # BOOM! Mệnh đề thuần M-variable
                            clause = [-solver.get_var('M', op_id, mach) for op_id, _ in subset]
                            solver.add_clause_smart(clause)