import sys
import os
import time
import gc
from collections import defaultdict

try:
    from pysat.formula import CNF
    from pysat.solvers import Solver
    from pysat.card import CardEnc, EncType
except ImportError:
    print("Error importing pysat")
    sys.exit(1)

from constraints.x import apply_x
from constraints_ver2.c2_ver2 import apply_c2_ver2
from constraints_ver2.c3_ver2 import apply_c3_ver2
from constraints_ver2.c4_ver2 import apply_c4_ver2
from constraints_ver2.c5_ver2 import apply_c5_ver2
from constraints_ver2.c6_c7_ver2 import apply_c6_c7_ver2
from constraints_ver2.energetic_exclusion import apply_energetic_exclusion
from constraints_ver2.incremental_ver2 import apply_incremental_ver2
from constraints.y import apply_y
from constraints.c2 import apply_c2
from constraints.c3 import apply_c3
from constraints.c4 import apply_c4
from constraints.c5 import apply_c5
from constraints.c6 import apply_c6
from constraints.c6_old import apply_c6_old
from constraints.c7 import apply_c7
from constraints.c7_old import apply_c7_old
from constraints.c4_old import apply_c4_old
from constraints.incremental import apply_incremental
from constraints.incremental_old import apply_incremental_old
from constraints.c7_new import apply_c7_new
from constraints.heuristic_start import apply_heuristic_start

class FJSSP_SAT:
    def __init__(self, jobs, num_machines, horizon, model_choice=3):
        self.incremental_func = None
        self.jobs = jobs
        self.num_machines = num_machines
        self.horizon = horizon
        self.model_choice = model_choice
        self.cnf = CNF()
        self.solver_instance = None
        self.ops = []
        self.job_map = []

        global_id = 0
        for j_idx, job in enumerate(jobs):
            current_job_ops = []
            for o_idx, op in enumerate(job):
                self.ops.append({'id': global_id, 'job_idx': j_idx, 'op_idx': o_idx, 'machines': op,
                                 'is_last': (o_idx == len(job) - 1)})
                current_job_ops.append(global_id)
                global_id += 1
            self.job_map.append(current_job_ops)

        self.num_ops = len(self.ops)
        self.var_map = {}
        self.var_count = 0
        self.min_p = [0] * self.num_ops
        self.est = [0] * self.num_ops
        self.lst = [0] * self.num_ops

    def get_var(self, name, *args):
        key = (name, *args)
        if key not in self.var_map:
            self.var_count += 1
            self.var_map[key] = self.var_count
        return self.var_map[key]

    def get_x_bounded(self, i, t):
        if t <= self.est[i]:
            return self.get_var('X', i, self.est[i])

        if t > self.lst[i]:
            return self.get_var('X', i, self.lst[i] + 1)

        return self.get_var('X', i, t)

    def neg(self, val):
        return -val

    def add_clause_smart(self, clause):
        if not clause and clause is not None:
            self.cnf.append([])
            if self.solver_instance: self.solver_instance.add_clause([])
            return
        self.cnf.append(clause)
        if self.solver_instance:
            self.solver_instance.add_clause(clause)

    def calculate_time_windows(self):
        for op in self.ops:
            self.min_p[op['id']] = min(p for m, p in op['machines'])

        for job_ids in self.job_map:
            current_est = 0
            for op_id in job_ids:
                self.est[op_id] = current_est
                current_est += self.min_p[op_id]

        for job_ids in self.job_map:
            current_budget = self.horizon
            for op_id in reversed(job_ids):
                current_budget -= self.min_p[op_id]
                self.lst[op_id] = current_budget

        for i in range(self.num_ops):
            self.add_clause_smart([self.get_var('X', i, self.est[i])])
            self.add_clause_smart([-self.get_var('X', i, self.lst[i] + 1)])

    def build_model_1(self):
        self.calculate_time_windows()
        apply_c2(self)
        apply_c3(self)
        apply_c4(self)
        apply_c5(self)
        apply_c6(self)
        apply_y(self)
        apply_c7_old(self)
        self.incremental_func = apply_incremental

    def build_model_2(self):
        self.calculate_time_windows()
        apply_c2(self)
        apply_c3(self)
        apply_c4(self)
        apply_c5(self)
        apply_c6_old(self)
        apply_y(self)
        apply_c7_old(self)
        self.incremental_func = apply_incremental

    def build_model_3(self):
        self.calculate_time_windows()
        apply_c2(self)
        apply_c3(self)
        apply_c4(self)
        apply_c5(self)
        apply_c6(self)
        apply_y(self)
        apply_c7(self)
        self.incremental_func = apply_incremental

    def build_model_4(self):
        self.calculate_time_windows()
        apply_c2(self)
        apply_c3(self)
        apply_c4(self)
        apply_c5(self)
        apply_c6_old(self)
        apply_y(self)
        apply_c7(self)
        self.incremental_func = apply_incremental

    def build_model_5(self):
        self.calculate_time_windows()
        apply_c2(self)
        apply_c3(self)
        apply_c4(self)
        apply_c5(self)
        apply_c6(self)
        apply_y(self)
        apply_c7_new(self)
        self.incremental_func = apply_incremental

    def build_model_6(self):
        self.calculate_time_windows()
        apply_heuristic_start(self)
        apply_c2(self)
        apply_c3(self)
        apply_c4(self)
        apply_c5(self)
        apply_c6(self)
        apply_y(self)
        apply_c7_new(self)
        self.incremental_func = apply_incremental_old

    def build_model_7(self):
        self.calculate_time_windows()
        apply_c2(self)
        apply_c3(self)
        apply_c4(self)
        apply_c5(self)
        apply_c6(self)
        apply_c7_old(self)
        self.incremental_func = apply_incremental

    def build_model_8(self):
        self.calculate_time_windows()
        apply_c2(self)
        apply_c3(self)
        apply_c4(self)
        apply_c5(self)
        apply_c6(self)
        apply_c7_old(self)
        self.incremental_func = apply_incremental_old

    def build_model_9(self):
        self.calculate_time_windows()
        apply_energetic_exclusion(self)
        apply_c2_ver2(self)
        apply_c3_ver2(self)
        apply_c4_ver2(self)
        apply_c5_ver2(self)
        apply_c6_c7_ver2(self)
        self.incremental_func = apply_incremental_ver2

    def constraint_incremental(self, new_limit):
        if hasattr(self, 'incremental_func') and callable(self.incremental_func):
            self.incremental_func(self, new_limit)
        else:
            apply_incremental_old(self, new_limit)

    def build_model(self):
        method_name = f"build_model_{self.model_choice}"
        build_method = getattr(self, method_name, None)

        if callable(build_method):
            build_method()
        else:
            raise ValueError(f"Lỗi logic: Hàm '{method_name}' chưa được định nghĩa trong class FJSSP_SAT.")

    def decode_model(self, model):
        model_set = set(model)
        schedule = []
        for i in range(self.num_ops):
            op_data = self.ops[i]
            selected_machine = -1
            duration = 0
            for mach, p in op_data['machines']:
                if self.get_var('M', i, mach) in model_set:
                    selected_machine = mach
                    duration = p
                    break
            start_time = -1
            for t in range(self.est[i], self.lst[i] + 1):
                if self.get_var('S', i, t) in model_set:
                    start_time = t
                    break
            if selected_machine != -1 and start_time != -1:
                schedule.append({
                    'id': i, 'job_idx': op_data['job_idx'], 'op_idx': op_data['op_idx'],
                    'machine': selected_machine, 'start': start_time, 'duration': duration, 'end': start_time + duration
                })
        schedule.sort(key=lambda x: x['start'])
        return schedule

    def solve_optimal(self, lb_threshold, time_out, test_name="unknown", log_dir=None):
        start_time = time.time()

        if log_dir is None:
            log_dir = os.path.join(os.getcwd(), "Log", test_name)
        os.makedirs(log_dir, exist_ok=True)

        trace_filename = os.path.join(log_dir, f"trace_{test_name}.log")
        trace_file = open(trace_filename, "w", encoding="utf-8")
        trace_file.write(f"START SOLVING | Test={test_name} | LB={lb_threshold} | Timeout={time_out}\n")
        trace_file.flush()
        os.fsync(trace_file.fileno())

        self.solver_instance = Solver(name='cadical195', bootstrap_with=self.cnf)
        best_schedule = None
        current_check_limit = self.horizon
        status = "UNKNOWN"
        last_print_time = start_time
        step = 0

        while True:
            step += 1
            trace_file.write(f"\n--- STEP {step} ---\n")
            trace_file.write(f"Target Limit: {current_check_limit}\n")

            trace_file.write(f"Stats | Số biến = {self.var_count} | Số mệnh đề = {len(self.cnf.clauses)}\n")

            elapsed_now = time.time() - start_time
            time_left = time_out - elapsed_now
            trace_file.write(f"Time left before solve: {time_left:.2f}s\n")

            trace_file.flush()
            os.fsync(trace_file.fileno())

            if elapsed_now - last_print_time >= 1.0:
                sys.stdout.write(
                    f"\r      -> Đang kiểm tra Makespan = {current_check_limit} | Số biến = {self.var_count} | Số mệnh đề = {len(self.cnf.clauses)} | T.gian: {int(elapsed_now)}/{int(time_out)}s")
                sys.stdout.flush()
                last_print_time = elapsed_now

            stats_before = self.solver_instance.accum_stats() if self.solver_instance else {}

            gc.disable()
            try:
                is_sat = self.solver_instance.solve()
            except Exception as e:
                is_sat = None
                trace_file.write(f"Exception caught during solve: {str(e)}\n")
            finally:
                gc.enable()
                gc.collect()

            stats_after = self.solver_instance.accum_stats() if self.solver_instance else {}
            conflicts = stats_after.get('conflicts', 0) - stats_before.get('conflicts', 0)
            propagations = stats_after.get('propagations', 0) - stats_before.get('propagations', 0)

            trace_file.write(f"Result (is_sat): {is_sat}\n")
            trace_file.write(f"Conflicts in step: {conflicts}\n")
            trace_file.write(f"Propagations in step: {propagations}\n")

            elapsed_now = time.time() - start_time

            if is_sat is None:
                status = "ERROR"
                break

            if is_sat:
                model = self.solver_instance.get_model()
                schedule = self.decode_model(model)
                best_schedule = schedule
                real_makespan = max(item['end'] for item in schedule)

                trace_file.write(f"Found Real Makespan: {real_makespan}\n")
                trace_file.flush()
                os.fsync(trace_file.fileno())

                if real_makespan <= lb_threshold:
                    status = "OPTIMAL"
                    trace_file.write(f"Hit Lower Bound ({lb_threshold}). Terminating.\n")
                    break

                new_limit = real_makespan - 1
                if new_limit < lb_threshold:
                    status = "OPTIMAL"
                    trace_file.write(f"New limit ({new_limit}) drops below LB ({lb_threshold}). Terminating.\n")
                    break

                trace_file.write(f"Pushing New Limit to: {new_limit}\n")
                self.constraint_incremental(new_limit)
                current_check_limit = new_limit
            else:
                status = "OPTIMAL" if best_schedule else "UNSAT"
                trace_file.write(f"UNSAT at current limit. Final status: {status}\n")
                break

        print()
        trace_file.write(f"\nFINAL STATUS: {status}\n")
        trace_file.write(f"TOTAL ELAPSED TIME: {(time.time() - start_time):.2f}s\n")
        trace_file.flush()
        trace_file.close()

        if self.solver_instance:
            self.solver_instance.delete()
            self.solver_instance = None
        return status, best_schedule, len(self.cnf.clauses), self.var_count