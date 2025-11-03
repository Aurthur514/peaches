def max_val(arr):
    """returs the second largest element in the array"""
    first = -1
    second = -1
    for num in arr:
        if num > first:
            second = first
            first = num
        elif num!= first and num > second:
            second = num
    return second

print(max_val([1,45,87,45,234,54,213])) 