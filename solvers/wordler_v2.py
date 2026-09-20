# wordle_entropy_bot.py
#
# Entropy-based Wordle solver.
#
# This is a separate solver from the frequency-based bot.
# It uses information theory to choose guesses:
#
#     H(G) = -sum(p_i * log2(p_i))
#
# where each p_i is the probability of receiving a particular
# feedback pattern from guess G.
#
# With no prior information, every remaining answer is treated
# as equally likely. Therefore:
#
#     p_i = bucket_size_i / number_of_remaining_answers
#
# The best guess is the one with the highest expected information gain.
#
# The solver can use a legal guess that is NOT currently a possible
# answer if that guess gives better information.

import math
import sys

# Allow us to import wordle.py
sys.path.append("../wordle")

from wordle import Wordle


def load_words(filename):
    """
    Load five-letter words from a text file.
    """

    words = []

    with open(filename, "r") as file:

        for line in file:

            word = line.strip().lower()

            if len(word) == 5:
                words.append(word)

    return words


class WordleEntropyBot:

    def __init__(self):

        # All possible answers
        self.answers = load_words("../data/answers.txt")

        # All legal guesses
        self.guesses = load_words("../data/guesses.txt")

        # Make sure every possible answer is also available
        # as a guess.
        self.guesses = list(dict.fromkeys(
            self.guesses + self.answers
        ))

        # At the beginning, every answer is possible
        self.possible_answers = self.answers.copy()

        self.turns_used = 0

        self.opening_guess = "salet"

    def update(self, guess, feedback):
        """
        Remove answers that are inconsistent with the feedback.
        """

        remaining_answers = []

        for answer in self.possible_answers:

            expected_feedback = self.get_feedback_pattern(
                guess,
                answer
            )

            if list(expected_feedback) == list(feedback):
                remaining_answers.append(answer)

        self.possible_answers = remaining_answers

        self.turns_used += 1

    def get_possible_answers(self):
        """
        Return the current list of possible answers.
        """

        return self.possible_answers

    def get_guess_stats(self, guess):
        """
        Compute both the entropy and the expected number of
        remaining candidates for a guess in a single pass over
        the possible answers, instead of two separate sweeps.

        Entropy:
            H = -sum(p * log2(p)) where p = bucket_size / total

        Expected remaining:
            E[remaining] = sum(bucket_size^2) / total

        Both numbers come from the same bucket counts, so there's
        no reason to compute them separately.
        """

        total = len(self.possible_answers)

        if total <= 1:
            return 0.0, 0.0

        counts = {}

        for answer in self.possible_answers:

            pattern = self.get_feedback_pattern(
                guess,
                answer
            )

            if pattern not in counts:
                counts[pattern] = 0

            counts[pattern] += 1

        entropy = 0.0
        sum_squared = 0

        for count in counts.values():

            probability = count / total

            entropy -= probability * math.log2(probability)

            sum_squared += count * count

        expected_remaining = sum_squared / total

        return entropy, expected_remaining

    def choose_guess(self):
        """
        Choose the guess with maximum entropy.

        Turn 1 always plays the precomputed opener (see
        self.opening_guess) since the full answer pool is
        identical at the start of every game.

        Later turns:
            Always search every legal guess. A small remaining
            pool is not the same as a splittable one: a family
            like batch/catch/hatch/latch/match/patch/watch all
            look identical to each other no matter which one you
            guess (guessing "batch" only ever says "yes" or "not
            batch" -- every other member gives the same "not
            batch" answer). The only way to actually separate
            them is a probe word from OUTSIDE the family, which
            means self.guesses has to stay in play even once the
            pool is small -- restricting the search to just the
            tied candidates at that point guarantees some of them
            are unreachable before turns run out. Searching all
            of self.guesses against a small pool is cheap (tens
            of thousands of comparisons, not millions), so there's
            no real cost to leaving it on.

        Tie-breaking:
            1. Higher entropy
            2. Lower expected number of remaining answers
            3. Prefer a word that is itself a possible answer

        If only one answer remains, simply play it.
        """

        if not self.possible_answers:
            return None

        if len(self.possible_answers) == 1:
            return self.possible_answers[0]

        if self.turns_used == 0:
            return self.opening_guess

        candidate_guesses = self.guesses

        best_word = None
        best_entropy = -1.0
        best_expected_remaining = float("inf")
        best_is_answer = False

        possible_set = set(self.possible_answers)

        for word in candidate_guesses:

            entropy, expected_remaining = self.get_guess_stats(word)

            if entropy > best_entropy + 1e-12:

                best_word = word
                best_entropy = entropy
                best_expected_remaining = expected_remaining
                best_is_answer = word in possible_set

            elif abs(entropy - best_entropy) <= 1e-12:

                is_answer = word in possible_set

                if expected_remaining < best_expected_remaining - 1e-12:

                    best_word = word
                    best_expected_remaining = expected_remaining
                    best_is_answer = is_answer

                elif (
                    abs(expected_remaining - best_expected_remaining) <= 1e-12
                    and is_answer
                    and not best_is_answer
                ):

                    best_word = word
                    best_is_answer = True

        return best_word

    def get_feedback_pattern(self, guess, answer):
        """
        Return Wordle feedback as:

            0 = gray
            1 = yellow
            2 = green

        The two-pass procedure correctly handles repeated letters.

        No caching here: with turn 1 hardcoded, the remaining turns
        work over much smaller pools, so a plain computation ends
        up faster overall than paying for a large, mostly-cold
        dict cache (and avoids the memory blow-up an unbounded
        guess x answer cache causes at this scale).
        """

        result = [0, 0, 0, 0, 0]

        answer_letters = list(answer)

        # First pass: greens
        for i in range(5):

            if guess[i] == answer[i]:

                result[i] = 2
                answer_letters[i] = None

        # Second pass: yellows
        for i in range(5):

            if result[i] == 0:

                if guess[i] in answer_letters:

                    result[i] = 1

                    index = answer_letters.index(
                        guess[i]
                    )

                    answer_letters[index] = None

        return tuple(result)


if __name__ == "__main__":

    bot = WordleEntropyBot()

    print("================================")
    print("WORDLE ENTROPY BOT")
    print("================================")
    print()

    print("This solver chooses guesses using Shannon entropy.")
    print()
    print("Enter feedback using:")
    print("G = Green")
    print("Y = Yellow")
    print("B = Gray")
    print()
    print("Example: GBBYB")
    print()

    for turn in range(6):

        guess = bot.choose_guess()

        print("Recommended guess:", guess)

        print(
            "Possible answers remaining:",
            len(bot.possible_answers)
        )

        if guess is not None and bot.turns_used > 0:
            entropy, _ = bot.get_guess_stats(guess)
            print(
                "Information entropy:",
                round(entropy, 4),
                "bits"
            )

        print()

        feedback_string = input(
            "Enter feedback: "
        ).strip().upper()

        if len(feedback_string) != 5:

            print(
                "Feedback must contain exactly 5 characters."
            )

            print()
            continue

        feedback = []

        valid_feedback = True

        for character in feedback_string:

            if character == "G":

                feedback.append(2)

            elif character == "Y":

                feedback.append(1)

            elif character == "B":

                feedback.append(0)

            else:

                valid_feedback = False

        if not valid_feedback:

            print("Use only G, Y, and B.")
            print()
            continue

        # Check whether the word was correct
        if feedback == [2, 2, 2, 2, 2]:

            print()
            print("The entropy bot solved the Wordle!")
            print("Answer:", guess)

            break

        bot.update(
            guess,
            feedback
        )

        print()

        if len(bot.possible_answers) == 0:

            print("No possible answers remain.")
            print("There may be an error in the feedback.")

            break

        print(
            "Possible answers remaining:",
            len(bot.possible_answers)
        )

        print()