from typing import List

def jump(arr: List[int]) -> int:
    """Find minimum number of jumps needed to reach the last element.
    
    Uses a greedy approach to achieve O(n) time complexity by tracking
    the current range that can be reached and the max range possible.
    
    Args:
        arr: List of integers where each element represents max jump length
            from that position
    
    Returns:
        int: Minimum number of jumps needed to reach last element, 
             or -1 if not possible
    """
    if not arr or arr[0] == 0:
        return -1
        
    n = len(arr)
    if n == 1:
        return 0
        
    # maxReach is the furthest index we can reach from current position
    # step is the steps we can take in current jump
    # jump is number of jumps needed
    maxReach = arr[0]
    step = arr[0]
    jump = 1
    
    for i in range(1, n):
        # If we've reached last element, return jumps
        if i == n - 1:
            return jump
            
        # Update the max reachable index
        maxReach = max(maxReach, i + arr[i])
        
        # We use a step to get to this position
        step -= 1
        
        # If no more steps are remaining
        if step == 0:
            # Must take a jump
            jump += 1
            
            # Check if the current position is the maximum reach
            if i >= maxReach:
                return -1
                
            # Get steps for the new jump
            step = maxReach - i

    return -1

# Test cases
test_cases = [
    [0,3,5,8,9,2,6,7,6,8,9],  # Original test case
    [1,3,5,8,9,2,6,7,6,8,9],  # Modified first element
    [2,3,1,1,4],              # Leetcode example
    [2,1],                    # Minimum case
    [1,1,1,1],               # Uniform jumps
    [0],                     # Single element
    [],                      # Empty array
]

for case in test_cases:
    print(f"Array: {case}")
    print(f"Minimum jumps: {jump(case)}\n")