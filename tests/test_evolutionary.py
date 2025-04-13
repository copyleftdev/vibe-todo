#!/usr/bin/env python3
"""
Evolutionary Testing for Todo App using DEAP
This test evolves payloads to find edge cases that might break the application.
"""
import random
import string
import json
import sqlite3
import time
import sys
import uuid
from deap import base, creator, tools, algorithms
from todo.models import init_db
from todo.controller import add_task, toggle_done, delete_task, list_tasks

# Constants for evolving payloads
MAX_TITLE_LENGTH = 20000  # Very large title to test limits
MAX_GENERATIONS = 50
POPULATION_SIZE = 100
SLA_THRESHOLD_MS = 10

# Specialized characters to test in payloads
SPECIAL_CHARS = [
    '\u0000',  # Null character
    '\u0001',  # Start of Heading
    '\u0007',  # Bell
    '\u001F',  # Unit Separator
    "\\",      # Backslash
    "'",       # Single quote
    '"',       # Double quote
    ';',       # Semicolon (used in SQL)
    '--',      # SQL comment
    '/*',      # SQL block comment start
    '{{',      # Template injection attempt
    '}}',      # Template injection attempt
    '<script>',  # XSS attempt
    '</script>', # XSS attempt
    '${',      # Shell injection
    '`',       # Backtick
    '\n',      # Newline
    '\r',      # Carriage return
    '\t',      # Tab
    '\b',      # Backspace
    '🔥',      # Unicode emoji
    '☢',       # Unicode symbol
    'درس',     # Arabic characters
    'Привет',  # Cyrillic characters
    '你好',    # Chinese characters
    '♜♞♝♛♚♝♞♜', # Chess pieces
    '0x1',     # Hex number
    '*' * 100,  # Repetition
]

# Define fitness goals - we want to maximize time taken and errors caused
creator.create("FitnessMax", base.Fitness, weights=(1.0, 100.0))  # Time and errors
creator.create("Individual", list, fitness=creator.FitnessMax)

def random_payload():
    """Generate a random payload that might stress the system"""
    payload_type = random.choice([
        "simple",
        "long",
        "special",
        "repeated",
        "mixed",
        "sql_injection",
        "null_bytes",
        "json_like",
        "extreme"
    ])
    
    if payload_type == "simple":
        # Just a simple string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 100)))
    
    elif payload_type == "long":
        # Very long string
        return ''.join(random.choices(string.ascii_letters, k=random.randint(1000, MAX_TITLE_LENGTH)))
    
    elif payload_type == "special":
        # Special characters
        return random.choice(SPECIAL_CHARS) * random.randint(1, 10)
    
    elif payload_type == "repeated":
        # Repeated patterns
        base_str = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 10)))
        return base_str * random.randint(10, 1000)
    
    elif payload_type == "mixed":
        # Mix of special chars and normal text
        normal = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 20)))
        special = random.choice(SPECIAL_CHARS)
        return normal + special + normal
    
    elif payload_type == "sql_injection":
        # SQL injection attempts
        return random.choice([
            "' OR 1=1 --",
            "'; DROP TABLE tasks; --",
            "' UNION SELECT * FROM sqlite_master; --",
            "'; UPDATE tasks SET done=1; --",
            "' || (SELECT sqlite_version()); --"
        ])
    
    elif payload_type == "null_bytes":
        # Strings with null bytes
        normal = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 20)))
        return normal + '\0' + normal
    
    elif payload_type == "json_like":
        # JSON-like content that might confuse parsers
        return json.dumps({
            "title": ''.join(random.choices(string.ascii_letters, k=5)),
            "command": random.choice(["add", "delete", "toggle"]),
            "id": str(uuid.uuid4())
        })
    
    elif payload_type == "extreme":
        # Combination of multiple attack vectors
        parts = []
        for _ in range(random.randint(2, 5)):
            parts.append(random_payload())
        return ''.join(parts)[:MAX_TITLE_LENGTH]
    
    return "fallback"

def mutate_payload(individual):
    """Mutate a payload to evolve it towards breaking the system"""
    mutation_type = random.choice([
        "replace",
        "insert",
        "delete",
        "combine",
        "repeat",
        "special"
    ])
    
    payload = ''.join(individual)
    
    if mutation_type == "replace" and payload:
        # Replace a character with a random one
        pos = random.randint(0, len(payload) - 1)
        new_char = random.choice(string.printable + ''.join(SPECIAL_CHARS))
        payload = payload[:pos] + new_char + payload[pos+1:]
    
    elif mutation_type == "insert" and len(payload) < MAX_TITLE_LENGTH:
        # Insert a special character
        pos = random.randint(0, len(payload))
        new_char = random.choice(string.printable + ''.join(SPECIAL_CHARS))
        payload = payload[:pos] + new_char + payload[pos:]
    
    elif mutation_type == "delete" and payload:
        # Delete a character
        pos = random.randint(0, len(payload) - 1)
        payload = payload[:pos] + payload[pos+1:]
    
    elif mutation_type == "combine":
        # Combine with another random payload
        other = random_payload()
        payload = payload + other
        payload = payload[:MAX_TITLE_LENGTH]  # Truncate if too long
    
    elif mutation_type == "repeat" and payload:
        # Repeat a section of the payload
        if len(payload) > 2:
            start = random.randint(0, len(payload) - 2)
            end = random.randint(start + 1, len(payload) - 1)
            section = payload[start:end]
            payload = payload + section
            payload = payload[:MAX_TITLE_LENGTH]  # Truncate if too long
    
    elif mutation_type == "special":
        # Insert a special string or character sequence
        special = random.choice([
            '\0',
            "'",
            "\\",
            "\\\\",
            "\\'",
            "\\\"",
            "\\n",
            "\\r",
            "\\t",
            "\\b",
            "\\u0000",
            "'--",
            "OR 1=1",
            "<script>alert('xss')</script>"
        ])
        pos = random.randint(0, len(payload))
        payload = payload[:pos] + special + payload[pos:]
        payload = payload[:MAX_TITLE_LENGTH]  # Truncate if too long
    
    # Convert back to list representation for DEAP
    return list(payload)

def crossover_payloads(ind1, ind2):
    """Crossover two payloads to create new test cases"""
    # Convert to strings for easier manipulation
    payload1 = ''.join(ind1)
    payload2 = ''.join(ind2)
    
    if not payload1 or not payload2:
        return ind1, ind2  # No change if either is empty
    
    # Choose crossover method
    method = random.choice(["single_point", "two_point", "uniform"])
    
    if method == "single_point":
        # Single point crossover
        point = random.randint(1, min(len(payload1), len(payload2)) - 1)
        new_payload1 = payload1[:point] + payload2[point:]
        new_payload2 = payload2[:point] + payload1[point:]
    
    elif method == "two_point" and len(payload1) > 2 and len(payload2) > 2:
        # Two point crossover
        point1 = random.randint(1, min(len(payload1), len(payload2)) - 2)
        point2 = random.randint(point1 + 1, min(len(payload1), len(payload2)) - 1)
        new_payload1 = payload1[:point1] + payload2[point1:point2] + payload1[point2:]
        new_payload2 = payload2[:point1] + payload1[point1:point2] + payload2[point2:]
    
    else:
        # Uniform crossover - randomly select from either parent
        new_payload1 = ""
        new_payload2 = ""
        for i in range(max(len(payload1), len(payload2))):
            if i < len(payload1) and i < len(payload2):
                if random.random() < 0.5:
                    new_payload1 += payload1[i]
                    new_payload2 += payload2[i]
                else:
                    new_payload1 += payload2[i]
                    new_payload2 += payload1[i]
            elif i < len(payload1):
                if random.random() < 0.5:
                    new_payload1 += payload1[i]
                    new_payload2 += payload1[i]
            elif i < len(payload2):
                if random.random() < 0.5:
                    new_payload1 += payload2[i]
                    new_payload2 += payload2[i]
    
    # Truncate if necessary
    new_payload1 = new_payload1[:MAX_TITLE_LENGTH]
    new_payload2 = new_payload2[:MAX_TITLE_LENGTH]
    
    # Convert back to list form for DEAP
    return list(new_payload1), list(new_payload2)

def evaluate_payload(individual):
    """
    Evaluate a payload by testing it against the todo app
    Returns a fitness tuple: (execution_time, errors_caused)
    """
    conn = init_db()
    payload = ''.join(individual)
    task_id = None
    execution_time = 0
    errors = 0
    
    # Test adding a task with the payload
    try:
        start_time = time.time()
        task = add_task(conn, payload)
        add_time = (time.time() - start_time) * 1000  # ms
        execution_time += add_time
        
        # Check if we've exceeded SLA threshold (this is good for finding problematic input)
        if add_time > SLA_THRESHOLD_MS:
            errors += 1
        
        task_id = task['id']
    except Exception as e:
        errors += 10  # Major error in add_task
        print(f"Error in add_task with payload: {payload[:50]}{'...' if len(payload) > 50 else ''}")
        print(f"Error type: {type(e).__name__}, Message: {str(e)}")
    
    # Test toggling the task if we created one
    if task_id:
        try:
            start_time = time.time()
            toggle_done(conn, task_id)
            toggle_time = (time.time() - start_time) * 1000  # ms
            execution_time += toggle_time
            
            if toggle_time > SLA_THRESHOLD_MS:
                errors += 1
        except Exception as e:
            errors += 5  # Error in toggle_done
            print(f"Error in toggle_done for task with payload: {payload[:50]}{'...' if len(payload) > 50 else ''}")
            print(f"Error type: {type(e).__name__}, Message: {str(e)}")
    
    # Test listing tasks
    try:
        start_time = time.time()
        tasks = list_tasks(conn)
        list_time = (time.time() - start_time) * 1000  # ms
        execution_time += list_time
        
        if list_time > SLA_THRESHOLD_MS:
            errors += 1
        
        # Check if the task is retrievable and correct
        if task_id:
            task_found = False
            for t in tasks:
                if t['id'] == task_id:
                    task_found = True
                    if t['title'] != payload:
                        errors += 2  # Data corruption or truncation
            
            if not task_found:
                errors += 3  # Task not found in listing
    except Exception as e:
        errors += 5  # Error in list_tasks
        print(f"Error in list_tasks after adding payload: {payload[:50]}{'...' if len(payload) > 50 else ''}")
        print(f"Error type: {type(e).__name__}, Message: {str(e)}")
    
    # Test deleting the task if we created one
    if task_id:
        try:
            start_time = time.time()
            delete_task(conn, task_id)
            delete_time = (time.time() - start_time) * 1000  # ms
            execution_time += delete_time
            
            if delete_time > SLA_THRESHOLD_MS:
                errors += 1
        except Exception as e:
            errors += 5  # Error in delete_task
            print(f"Error in delete_task for task with payload: {payload[:50]}{'...' if len(payload) > 50 else ''}")
            print(f"Error type: {type(e).__name__}, Message: {str(e)}")
    
    conn.close()
    
    # Return fitness values: (execution_time, errors_caused)
    return execution_time, errors

def log_result(payload, fitness, generation, individual_idx):
    """Log a problematic payload and its effects"""
    execution_time, errors = fitness
    
    result = {
        "generation": generation,
        "individual": individual_idx,
        "payload_length": len(payload),
        "payload_preview": payload[:100] + ('...' if len(payload) > 100 else ''),
        "execution_time_ms": execution_time,
        "errors_caused": errors,
        "sla_violation": execution_time > SLA_THRESHOLD_MS,
        "timestamp": time.time()
    }
    
    # Add full payload for significant findings
    if errors > 0 or execution_time > SLA_THRESHOLD_MS:
        result["full_payload"] = payload
        
        # For very interesting payloads, save to a separate file
        if errors >= 5 or execution_time > SLA_THRESHOLD_MS * 2:
            try:
                with open(f"reports/evolved_payload_{generation}_{individual_idx}.txt", "w") as f:
                    f.write(payload)
            except:
                pass  # Ignore file writing errors
    
    print(json.dumps(result))
    return result

def run_evolutionary_test(max_generations=MAX_GENERATIONS):
    """Run the evolutionary test to find problematic inputs"""
    # Initialize DEAP toolbox
    toolbox = base.Toolbox()
    
    # Register initialization, mutation, crossover and selection
    toolbox.register("payload_char", random.choice, string.printable + ''.join(SPECIAL_CHARS))
    toolbox.register("individual", tools.initRepeat, creator.Individual, 
                    toolbox.payload_char, n=random.randint(1, 100))
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    # Alternative initialization with pre-defined payloads
    def init_individual(ind_class):
        return ind_class(list(random_payload()))
    
    toolbox.register("individual_guess", init_individual, creator.Individual)
    toolbox.register("population_guess", tools.initRepeat, list, toolbox.individual_guess)
    
    # Register genetic operators
    toolbox.register("evaluate", evaluate_payload)
    toolbox.register("mate", crossover_payloads)
    toolbox.register("mutate", mutate_payload)
    toolbox.register("select", tools.selTournament, tournsize=3)
    
    # Create initial population
    population = toolbox.population_guess(n=POPULATION_SIZE)
    
    # Evaluate initial population
    print(json.dumps({"operation": "evolutionary_test", "status": "starting", "population_size": POPULATION_SIZE, "max_generations": max_generations}))
    
    fitnesses = list(map(toolbox.evaluate, population))
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit
    
    # Log initial population
    gen = 0
    for i, ind in enumerate(population):
        payload = ''.join(ind)
        log_result(payload, ind.fitness.values, gen, i)
    
    # Begin the evolution
    for gen in range(1, max_generations + 1):
        print(json.dumps({"operation": "evolutionary_test", "status": "generation_start", "generation": gen}))
        
        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))
        
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        
        # Apply crossover
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.7:  # 70% chance of crossover
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        
        # Apply mutation
        for mutant in offspring:
            if random.random() < 0.3:  # 30% chance of mutation
                toolbox.mutate(mutant)
                del mutant.fitness.values
        
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Replace the old population
        population[:] = offspring
        
        # Log results for this generation
        for i, ind in enumerate(population):
            payload = ''.join(ind)
            log_result(payload, ind.fitness.values, gen, i)
        
        print(json.dumps({"operation": "evolutionary_test", "status": "generation_complete", "generation": gen}))
    
    # Return the final population
    print(json.dumps({"operation": "evolutionary_test", "status": "completed", "total_generations": max_generations}))
    return population

def analyze_results(population):
    """Analyze the final population for insights"""
    # Find best individual
    best_ind = tools.selBest(population, 1)[0]
    best_payload = ''.join(best_ind)
    execution_time, errors = best_ind.fitness.values
    
    print(json.dumps({
        "operation": "analysis", 
        "best_payload_length": len(best_payload),
        "best_payload_preview": best_payload[:100] + ('...' if len(best_payload) > 100 else ''),
        "best_execution_time": execution_time,
        "best_errors": errors
    }))
    
    # Save best payload
    try:
        with open("reports/best_evolved_payload.txt", "w") as f:
            f.write(best_payload)
    except:
        pass  # Ignore file writing errors
    
    # Analyze payload patterns
    patterns = {}
    for ind in tools.selBest(population, 10):
        payload = ''.join(ind)
        
        # Check for SQL injection patterns
        if "'" in payload or '"' in payload:
            patterns.setdefault("sql_injection", 0)
            patterns["sql_injection"] += 1
        
        # Check for long payloads
        if len(payload) > 1000:
            patterns.setdefault("long_payload", 0)
            patterns["long_payload"] += 1
        
        # Check for special characters
        for char in SPECIAL_CHARS:
            if char in payload:
                patterns.setdefault("special_chars", 0)
                patterns["special_chars"] += 1
                break
        
        # Check for null bytes
        if '\0' in payload:
            patterns.setdefault("null_bytes", 0)
            patterns["null_bytes"] += 1
    
    print(json.dumps({
        "operation": "pattern_analysis",
        "patterns": patterns
    }))
    
    return best_ind

if __name__ == "__main__":
    # Create reports directory if it doesn't exist
    import os
    os.makedirs("reports", exist_ok=True)
    
    # Run the evolutionary test
    final_population = run_evolutionary_test()
    
    # Analyze results
    best_payload = analyze_results(final_population)
    
    print(json.dumps({
        "operation": "evolutionary_test_suite",
        "status": "completed",
        "best_fitness": best_payload.fitness.values
    }))
