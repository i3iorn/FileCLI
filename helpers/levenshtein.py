class Levenshtein:
    @classmethod
    def distance(cls, s1: str, s2: str, limit: int = 10) -> int:
        """
        Calculates the Levenshtein distance between two strings.

        # Parameters
        s1 (str): The first string to compare.
        s2 (str): The second string to compare.
        limit (int): The maximum distance to calculate.

        # Returns
        int: The Levenshtein distance between the two strings.
        """
        s1 = s1.strip()
        s2 = s2.strip()
        if len(s1) > len(s2):
            s1, s2 = s2, s1
        distances = range(len(s1) + 1)
        for index2, char2 in enumerate(s2):
            if index2 > limit:
                return limit + 1
            new_distances = [index2 + 1]
            for index1, char1 in enumerate(s1):
                if index1 > limit:
                    return limit + 1
                if char1 == char2:
                    new_distances.append(distances[index1])
                else:
                    new_distances.append(1 + min((distances[index1], distances[index1 + 1], new_distances[-1])))
            distances = new_distances
        return distances[-1]
