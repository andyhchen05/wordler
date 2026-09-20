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

        # Shared across every WordleEntropyBot instance, not just
        # this one. evaluate_word() creates a fresh bot per answer,
        # but the opener is fixed, so there are at most 243 distinct
        # turn-2 states (one per feedback pattern from the opener) --
        # and with 3209 answers, each state recurs roughly 13 times
        # on average. Caching by the pool itself (not by individual
        # guess/answer pairs) means the second, third, ... occurrence
        # of the same state across DIFFERENT games can skip the
        # search entirely instead of recomputing it from scratch.
        if not hasattr(WordleEntropyBot, "_stats_cache"):
            WordleEntropyBot._stats_cache = {}
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

    def get_guess_stats(self, guess, pool_key):
        """
        Compute both the entropy and the expected number of
        remaining candidates for a guess in a single pass over
        the possible answers, instead of two separate sweeps.

        pool_key identifies the current possible_answers state
        (see choose_guess). Only turn 2 passes a real pool_key --
        with a fixed opener there are at most 243 distinct turn-2
        states shared across all 3209 games, so caching those
        specifically gives most of the reuse benefit while keeping
        the cache small. Later turns have far more varied, less
        reused states, so they pass pool_key=None and skip caching
        entirely rather than growing the cache for little payoff.

        Entropy:
            H = -sum(p * log2(p)) where p = bucket_size / total

        Expected remaining:
            E[remaining] = sum(bucket_size^2) / total
        """

        use_cache = pool_key is not None
        cache_key = (guess, pool_key)

        if use_cache and cache_key in WordleEntropyBot._stats_cache:
            return WordleEntropyBot._stats_cache[cache_key]

        total = len(self.possible_answers)

        if total <= 1:
            result = (0.0, 0.0)
            if use_cache:
                WordleEntropyBot._stats_cache[cache_key] = result
            return result

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

        result = (entropy, expected_remaining)

        if use_cache:
            WordleEntropyBot._stats_cache[cache_key] = result

        return result

    def choose_guess(self):
        """
        Choose the guess with maximum entropy.

        Turn 1 always plays the precomputed opener (see
        self.opening_guess) since the full answer pool is
        identical at the start of every game.

        Later turns: search every legal guess (self.guesses
        already includes every possible answer too, so this
        always considers real answers as well as pure probes).
        Turn 2 specifically is cached across every bot instance
        (there are at most 243 distinct turn-2 states no matter
        what, since the opener is fixed) -- see get_guess_stats.

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

        pool_key = frozenset(self.possible_answers) if self.turns_used == 1 else None

        best = self._scan(self.guesses, pool_key)

        return best[0]

    def _scan(self, pool, pool_key):
        """
        Search a pool of candidate guesses and return whichever
        one wins under the tie-break rules, as
        (word, entropy, expected_remaining, is_answer).
        """

        possible_set = set(self.possible_answers)

        best = None

        for word in pool:

            entropy, expected_remaining = self.get_guess_stats(
                word,
                pool_key
            )

            candidate = (
                word,
                entropy,
                expected_remaining,
                word in possible_set
            )

            if best is None:
                best = candidate
            else:
                best = self._better(best, candidate)

        return best

    def _better(self, a, b):
        """
        Given two (word, entropy, expected_remaining, is_answer)
        tuples, return whichever wins under the same tie-break
        rules choose_guess has always used:

            1. Higher entropy
            2. Lower expected number of remaining answers
            3. Prefer a word that is itself a possible answer
        """

        _, a_entropy, a_expected, a_is_answer = a
        _, b_entropy, b_expected, b_is_answer = b

        if b_entropy > a_entropy + 1e-12:
            return b

        if a_entropy > b_entropy + 1e-12:
            return a

        if b_expected < a_expected - 1e-12:
            return b

        if a_expected < b_expected - 1e-12:
            return a

        if b_is_answer and not a_is_answer:
            return b

        return a

    def get_feedback_pattern(self, guess, answer):
        """
        Return Wordle feedback as:

            0 = gray
            1 = yellow
            2 = green

        The two-pass procedure correctly handles repeated letters.
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
            pool_key = frozenset(bot.possible_answers) if bot.turns_used == 1 else None
            entropy, _ = bot.get_guess_stats(guess, pool_key)
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