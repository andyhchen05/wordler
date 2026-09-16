import matplotlib.pyplot as plt


def load_words(filename):
    """
    Load all five-letter words from a file.
    """

    words = []

    with open(filename, "r") as file:

        for line in file:

            word = line.strip().lower()

            if len(word) == 5:
                words.append(word)

    return words


def count_letter_occurrences(words):
    """
    Count the total number of times
    each letter appears.
    """

    counts = {}

    for letter in "abcdefghijklmnopqrstuvwxyz":
        counts[letter] = 0

    for word in words:

        for letter in word:
            counts[letter] += 1

    return counts


def count_words_containing_letter(words):
    """
    Count how many words contain each letter
    at least once.
    """

    counts = {}

    for letter in "abcdefghijklmnopqrstuvwxyz":
        counts[letter] = 0

    for word in words:

        unique_letters = set(word)

        for letter in unique_letters:
            counts[letter] += 1

    return counts


def count_letter_positions(words):
    """
    Count how often each letter appears
    in each position.
    """

    positions = {}

    for letter in "abcdefghijklmnopqrstuvwxyz":
        positions[letter] = [0, 0, 0, 0, 0]

    for word in words:

        for position in range(5):

            letter = word[position]

            positions[letter][position] += 1

    return positions


def calculate_position_probabilities(positions, total_words):
    """
    Calculate the probability of each letter
    appearing in each position.
    """

    probabilities = {}

    for letter in "abcdefghijklmnopqrstuvwxyz":

        probabilities[letter] = []

        for position in range(5):

            count = positions[letter][position]

            probability = count / total_words

            probabilities[letter].append(probability)

    return probabilities


def plot_frequency(counts, title, ylabel):
    """
    Create a bar chart of letter frequencies.
    """

    letters = list(counts.keys())
    values = list(counts.values())

    plt.figure(figsize=(12, 6))

    plt.bar(letters, values)

    plt.xlabel("Letter")
    plt.ylabel(ylabel)
    plt.title(title)

    plt.tight_layout()
    plt.show()


def plot_position_heatmap(positions):
    """
    Create a heatmap showing where letters
    appear in five-letter answers.
    """

    letters = list("abcdefghijklmnopqrstuvwxyz")

    data = []

    for letter in letters:
        data.append(positions[letter])

    plt.figure(figsize=(10, 12))

    plt.imshow(data, aspect="auto")

    plt.xticks(
        range(5),
        ["Position 1", "Position 2", "Position 3",
         "Position 4", "Position 5"]
    )

    plt.yticks(
        range(26),
        [letter.upper() for letter in letters]
    )

    plt.xlabel("Position")
    plt.ylabel("Letter")
    plt.title("Letter Frequency by Position")

    plt.colorbar(label="Occurrences")

    plt.tight_layout()
    plt.show()


def count_unique_letter_counts(words):
    counts = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0
    }

    for word in words:
        unique_count = len(set(word))
        counts[unique_count] += 1

    return counts


def print_unique_letter_counts(counts, total_words):
    print()
    print("Unique letters per answer:")
    print("--------------------------")

    for unique_count in range(5, 0, -1):
        count = counts[unique_count]
        percentage = (count / total_words) * 100

        print(
            "{} unique letters: {} ({:.2f}%)".format(
                unique_count,
                count,
                percentage
            )
        )


if __name__ == "__main__":

    # ------------------------------------------------
    # LOAD ANSWERS
    # ------------------------------------------------

    words = load_words("../data/answers.txt")

    total_words = len(words)

    print("Number of answers:", total_words)
    print()

    # ------------------------------------------------
    # TOTAL LETTER OCCURRENCES
    # ------------------------------------------------

    occurrence_counts = count_letter_occurrences(words)

    print("Total letter occurrences:")
    print()

    for letter, count in occurrence_counts.items():

        print(
            "{}: {}".format(letter.upper(), count)
        )

    print()

    # ------------------------------------------------
    # WORDS CONTAINING EACH LETTER
    # ------------------------------------------------

    word_counts = count_words_containing_letter(words)

    print("Number of answers containing each letter:")
    print()

    for letter, count in word_counts.items():

        print(
            "{}: {}".format(letter.upper(), count)
        )

    print()

    # ------------------------------------------------
    # LETTER FREQUENCY BY POSITION
    # ------------------------------------------------

    position_counts = count_letter_positions(words)

    print("Letter frequency by position:")
    print()

    print(
        "{:<8} {:>10} {:>10} {:>10} {:>10} {:>10}".format(
            "Letter",
            "Pos 1",
            "Pos 2",
            "Pos 3",
            "Pos 4",
            "Pos 5"
        )
    )

    print("-" * 60)

    for letter in "abcdefghijklmnopqrstuvwxyz":

        counts = position_counts[letter]

        print(
            "{:<8} {:>10} {:>10} {:>10} {:>10} {:>10}".format(
                letter.upper(),
                counts[0],
                counts[1],
                counts[2],
                counts[3],
                counts[4]
            )
        )

    print()

    # ------------------------------------------------
    # POSITION PROBABILITIES
    # ------------------------------------------------

    position_probabilities = calculate_position_probabilities(
        position_counts,
        total_words
    )

    print("Letter probability by position:")
    print()

    print(
        "{:<8} {:>10} {:>10} {:>10} {:>10} {:>10}".format(
            "Letter",
            "Pos 1",
            "Pos 2",
            "Pos 3",
            "Pos 4",
            "Pos 5"
        )
    )

    print("-" * 60)

    for letter in "abcdefghijklmnopqrstuvwxyz":

        probabilities = position_probabilities[letter]

        print(
            "{:<8} {:>9.2f}% {:>9.2f}% {:>9.2f}% {:>9.2f}% {:>9.2f}%".format(
                letter.upper(),
                probabilities[0] * 100,
                probabilities[1] * 100,
                probabilities[2] * 100,
                probabilities[3] * 100,
                probabilities[4] * 100
            )
        )

    unique_letter_counts = count_unique_letter_counts(words)

    print_unique_letter_counts(
        unique_letter_counts,
        len(words)
    )

    # ------------------------------------------------
    # PLOTS
    # ------------------------------------------------

    plot_frequency(
        occurrence_counts,
        "Letter Frequency in Wordle Answers",
        "Total occurrences"
    )

    plot_frequency(
        word_counts,
        "Letters Appearing in Wordle Answers",
        "Number of answers"
    )

    plot_position_heatmap(position_counts)