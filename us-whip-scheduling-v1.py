import random
from operator import itemgetter
    
#get max run time for a given job at a given workstation
def largest_runtime(job,workstation,run_times):
    max_run_length = 0
    for omega in range(len(run_times)):
        #run_times is list of nested dictionaries. 
        #Each dict in the list is a scenario
        max_run_length = max(run_times[omega][workstation][job], max_run_length)
    return max_run_length

def expected_runtime(job,workstation,run_times):
    sum = 0
    for omega in range(len(run_times)):
        #run_times is list of nested dictionaries. 
        #Each dict in the list is a scenario
        sum+= run_times[omega][workstation][job]
    return sum/len(run_times)

#evaluate candidate solution
def evaluate_solution(candidate, due_dates, run_times, num_workstations):
#x_i,j,t: 2 workstations, 3 jobs, 3 time
#[000, 100, 010, 110, 020, 120, 001, 101, 011, 111, 021, 121, 002, 102, 012, 112, 022, 122]
    num_jobs = len(due_dates)    

    #check that the solution is feasible. We add a penalty for infeasibility
    for i in range(num_workstations):
        for j in range(num_jobs):
            for t in range(len(candidate[0][0])):
                #if a job starts at a workstation at a timne
                if candidate[i][j][t] == 1:
                    #get the largest runtime for that job/workstation
                    max_runtime = largest_runtime(j,i,run_times)
                    #check that nothing else starts at a workstation until the current job is done
                    for j_prime in range(num_jobs):
                        for t_delta in range(max_runtime):
                            #ensure we dont go over the max time
                            if t+t_delta >= len(candidate[0][0]):
                                break
                            if candidate[i][j_prime][t+t_delta] == 1 and j_prime != j:
                                return 10000

                    #check that a job does not start at the next workstation
                    #until it is done at the current workstation
                    for i_prime in range(i, num_workstations):
                        for t_delta in range(max_runtime):
                            #ensure we dont go over the max time
                            if t+t_delta >= len(candidate[0][0]):
                                break
                            if candidate[i_prime][j][t + t_delta] == 1 and i_prime != i:
                                return 20000
        #ensure that each job goes through each workstation once and only once
        for j in range(num_jobs):
            sum_of_job = 0
            for i in range(num_workstations):
                sum = 0
                for t in range(len(candidate[0][0])):
                    sum += candidate[i][j][t]
                    sum_of_job += candidate[i][j][t]
                if sum > 1: return 30000
            if sum_of_job != num_workstations:
                return 40000

    #find total time overdue
    val = 0
    #check last workstation for each job
    for j in range(num_jobs):
        for t in range(len(candidate[0][0])):  
            #check if a final workstation is set to true
            if candidate[num_workstations-1][j][t] == 1:

                #loop through run times to get largest possible run time 
                #of the last workstation to add to the start time of the last 
                #workstation to get competion time
                max_runtime = expected_runtime(j, num_workstations-1, run_times)
                if due_dates[j] < t + max_runtime:
                    val += (t + max_runtime) - due_dates[j]
    return val
    
#generate candidate solution
def get_random_solution(num_workstations, num_jobs, num_times, due_dates, run_times):
    vec = []
    for i in range(num_workstations):
        job_vec = []
        for j in range(num_jobs):
            times_vec = []
            for t in range(num_times):
                times_vec.append(random.randint(0,1))
            job_vec.append(times_vec)
        vec.append(job_vec)
    solution = {}
    solution['vec'] = vec
    solution['val'] = evaluate_solution(vec, due_dates, run_times, num_workstations)
    return solution

def mutate(father, mother, due_dates, run_times, num_workstations, crossover_threshold = 0.7):
    child1_vec = []
    child2_vec = []
    for i in range(len(father['vec'])):
        child1_job_vec = []
        child2_job_vec = []
        for j in range(len(father['vec'][0])):
            child1_time_vec = []
            child2_time_vec = []
            for t in range(len(father['vec'][0][0])):
                crossover = random.random()
                if crossover > crossover_threshold:
                    child1_time_vec.append(mother['vec'][i][j][t])
                    child2_time_vec.append(father['vec'][i][j][t])
                else:
                    child1_time_vec.append(father['vec'][i][j][t])
                    child2_time_vec.append(mother['vec'][i][j][t]) 
            child1_job_vec.append(child1_time_vec)
            child2_job_vec.append(child2_time_vec)
        child1_vec.append(child1_job_vec)
        child2_vec.append(child2_job_vec)
    child1_val = evaluate_solution(child1_vec, due_dates, run_times, num_workstations)
    child2_val = evaluate_solution(child2_vec, due_dates, run_times, num_workstations)
    candidate = {}
    if child1_val > child2_val:
        candidate['val'] = child1_val
        candidate['vec'] = child1_vec
        return candidate
    candidate['val'] = child2_val
    candidate['vec'] = child2_vec
    return candidate

def run_genetic(due_dates, run_times, num_times, generation_size = 1000, 
                elitist_size = 100, immigrant_size = 100, num_iterations = 5000, print_every = 500, seed = None):
    num_jobs = len(due_dates)
    num_workstations = len(run_times[0])

    #generate initial population if no seed
    current_gen = []
    if seed == None:
        for k in range(generation_size):
            current_gen.append(get_random_solution(num_workstations, num_jobs, num_times,due_dates, run_times))
    else:
        current_gen = seed

    for k in range(num_iterations):
        current_gen = sorted(current_gen, key=itemgetter('val'))
        if k % print_every == 0:
            print('Best solution after ' + str(k) + ' generations: ' + str(current_gen[0]['val']))
        next_gen = current_gen[:elitist_size]
        for i in range(immigrant_size):
            next_gen.append(get_random_solution(num_workstations, num_jobs, num_times, due_dates, run_times))
        for i in range(generation_size - elitist_size - immigrant_size):
            father = current_gen[random.randint(0, generation_size-1)]
            mother = current_gen[random.randint(0, generation_size-1)]
            child = mutate(mother,father,due_dates,run_times,num_workstations)
            next_gen.append(child)
        current_gen = next_gen

    
    final_sorted = sorted(current_gen, key=itemgetter('val'))
    return final_sorted[0]
            
        







#test that candidate evaluation is correct
candidate_vec = [
    [
        [1,0,0,0,0,0,0,0,0,0], #i = 0, j = 0
        [0,0,1,0,0,0,0,0,0,0]  #i = 0, j = 1
    ],
    [
        [0,0,0,1,0,0,0,0,0,0], #i = 1, j = 0
        [0,0,0,0,0,0,0,0,0,1]  #i = 1, j = 1
    ]
]
due_dates = [5, 7]
run_times = [
            [[2,1],[2,4]],
            [[1,3],[3,3]]
            ]

num_workstations = 2


candidate = {}
candidate['vec'] = candidate_vec
candidate['val'] = evaluate_solution(candidate_vec, due_dates, run_times, num_workstations)

print(candidate['val'])

seed = []
seed.append(candidate)
for k in range(999):
    seed.append(get_random_solution(num_workstations, 2, 10 ,due_dates, run_times))

sln = run_genetic(due_dates, run_times, 10, seed = seed)

print(sln)
