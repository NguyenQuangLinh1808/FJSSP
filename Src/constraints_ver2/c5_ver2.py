from pysat.card import CardEnc, EncType

def apply_c5_ver2(solver):
    for i in range(solver.num_ops):
        lits = [solver.get_var('M', i, m) for m, p in solver.ops[i]['machines']]

        n_mach = len(lits)
        if n_mach == 1:
            # Chỉ có 1 lựa chọn -> Ép Unit Clause
            solver.add_clause_smart([lits[0]])
        elif n_mach == 2:
            # Chỉ có 2 lựa chọn -> Dùng logic mệnh đề cơ bản (XOR), loại bỏ chi phí của Totalizer
            solver.add_clause_smart([lits[0], lits[1]])  # At least one
            solver.add_clause_smart([-lits[0], -lits[1]])  # At most one
        else:
            # Từ 3 lựa chọn trở lên mới dùng Totalizer Encoding
            cnf_clauses = CardEnc.equals(lits=lits, bound=1, top_id=solver.var_count, encoding=EncType.totalizer)
            for clause in cnf_clauses:
                solver.add_clause_smart(clause)
                for lit in clause:
                    solver.var_count = max(solver.var_count, abs(lit))