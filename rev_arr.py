def rev_arr(arr):
    """returns the reversed array"""
    start = 0
    end = len(arr) - 1
    while start < end:
        arr[start], arr[end] = arr[end], arr[start]
        start += 1
        end -= 1
    return arr

returned_array = rev_arr([1, 2, 3, 4, 5,98765,24567,0,234,987,45,765,123,876,543,234,890,345,678,1234,5678,91011])
print(returned_array)