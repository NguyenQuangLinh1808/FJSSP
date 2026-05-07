from pysat.card import CardEnc, EncType

def apply_c5_ver2(solver):
    for i in range(solver.num_ops):
        lits = [solver.get_var('M', i, m) for m, p in solver.ops[i]['machines']]
        cnf_clauses = CardEnc.equals(lits=lits, bound=1, top_id=solver.var_count, encoding=EncType.totalizer)
        for clause in cnf_clauses:
            solver.add_clause_smart(clause)
            for lit in clause:
                solver.var_count = max(solver.var_count, abs(lit))