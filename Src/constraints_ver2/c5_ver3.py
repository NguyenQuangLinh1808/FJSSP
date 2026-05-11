from pysat.card import CardEnc, EncType

def apply_c5_ver3(solver):
    """
    Ràng buộc chọn 1 máy (Exactly-One) tối ưu hóa.
    - 1 máy: Ép True
    - 2 máy: XOR
    - 3, 4 máy: Pairwise AMO (Không sinh biến phụ)
    - >= 5 máy: Totalizer Encoding
    """
    for i in range(solver.num_ops):
        lits = [solver.get_var('M', i, m) for m, p in solver.ops[i]['machines']]
        n = len(lits)

        if n == 1:
            solver.add_clause_smart([lits[0]])
        elif n == 2:
            solver.add_clause_smart([lits[0], lits[1]])
            solver.add_clause_smart([-lits[0], -lits[1]])
        elif n <= 4:
            solver.add_clause_smart(lits)  # At-least-one
            for x in range(n):
                for y in range(x + 1, n):
                    solver.add_clause_smart([-lits[x], -lits[y]])  # At-most-one
        else:
            cnf_clauses = CardEnc.equals(
                lits=lits, bound=1,
                top_id=solver.var_count,
                encoding=EncType.totalizer
            )
            for clause in cnf_clauses:
                solver.add_clause_smart(clause)
                for lit in clause:
                    solver.var_count = max(solver.var_count, abs(lit))