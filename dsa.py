import heapq


class ComplaintPriorityQueue:

    def __init__(self):
        self.complaints = []

    def add_complaint(self, complaint):

        priority_order = {
            "High": 1,
            "Medium": 2,
            "Low": 3
        }

        priority = priority_order.get(complaint[5], 2)

        heapq.heappush(
            self.complaints,
            (priority, complaint[0], complaint)
        )

    def show_complaints(self):

        sorted_complaints = sorted(self.complaints)

        return [item[2] for item in sorted_complaints]
    # Hash Map for Complaint ID Search

class ComplaintHashMap:

    def __init__(self):
        self.complaints = {}

    # Add complaint
    def add_complaint(self, complaint):
        complaint_id = complaint[0]
        self.complaints[complaint_id] = complaint

    # Search complaint by ID
    def search_complaint(self, complaint_id):
        return self.complaints.get(complaint_id)

    # Display all complaints
    def show_all_complaints(self):
        return list(self.complaints.values())
    
    # Merge Sort for sorting complaints by ID

def merge_sort_complaints(complaints):

    if len(complaints) <= 1:
        return complaints

    mid = len(complaints) // 2

    left = merge_sort_complaints(complaints[:mid])
    right = merge_sort_complaints(complaints[mid:])

    return merge(left, right)


def merge(left, right):

    result = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):

        if left[i][0] <= right[j][0]:
            result.append(left[i])
            i += 1

        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    return result

# Queue for handling complaints in FIFO order

class ComplaintQueue:

    def __init__(self):
        self.complaints = []

    def add_complaint(self, complaint):
        self.complaints.append(complaint)

    def process_complaint(self):
        if self.complaints:
            return self.complaints.pop(0)

        return None

    def show_queue(self):
        return self.complaints