# wordle_bot.py

import math
import sys

# Allow us to import wordle.py
sys.path.append("../wordle")

from wordle import Wordle


def load_words(filename):
    """
    Load words from a text file.
    """

    words = []

    with open(filename, "r") as file:

        for line in file:

            word = line.strip().lower()

            if len(word) == 5:
                words.append(word)

    return words


class WordleBot:

    def __init__(self):

        # All possible answers
        self.answers = load_words("../data/answers.txt")

        # All legal guesses
        self.guesses = load_words("../data/guesses.txt")

        # At the beginning, every answer is possible
        self.possible_answers = self.answers.copy()


    def update(self, guess, feedback):
        """
        Remove answers that are inconsistent
        with the feedback.
        """

        remaining_answers = []

        for answer in self.possible_answers:

            game = Wordle(answer)

            expected_feedback = game.get_feedback(guess)

            if expected_feedback == feedback:

                remaining_answers.append(answer)

        self.possible_answers = remaining_answers


    def get_possible_answers(self):
        """
        Return the current list of possible answers.
        """

        return self.possible_answers


    def get_letter_frequencies(self):
        """
        Count how often each letter appears
        in the remaining possible answers.

        A repeated letter in one word is only counted once.
        This rewards guessing letters that are likely to be
        SOMEWHERE in the answer (yellow/green potential).
        """

        frequencies = {}

        for word in self.possible_answers:

            unique_letters = set(word)

            for letter in unique_letters:

                if letter not in frequencies:
                    frequencies[letter] = 0

                frequencies[letter] += 1

        return frequencies


    def get_position_frequencies(self):
        """
        For each of the 5 positions, count how often each
        letter appears in that position among the remaining
        possible answers. This rewards guessing letters that
        are likely to be correct in that EXACT spot (green
        potential), which plain letter frequency can't see.
        """

        position_frequencies = [{} for _ in range(5)]

        for word in self.possible_answers:

            for position, letter in enumerate(word):

                counts = position_frequencies[position]

                if letter not in counts:
                    counts[letter] = 0

                counts[letter] += 1

        return position_frequencies


    def score_word(self, word, frequencies, position_frequencies):
        """
        Give a word a score based on:
          - how often its (unique) letters appear anywhere
            among the possible answers, plus
          - how often each of its letters appears in that
            exact position among the possible answers.

        The two signals are complementary: letter frequency
        rewards words that are likely to turn up yellow/green
        information about presence; position frequency rewards
        words likely to land greens, which is what lets the bot
        tell apart words that share the same letters (e.g.
        catch/match/patch/watch) instead of guessing blind
        among them.
        """

        score = 0

        unique_letters = set(word)

        for letter in unique_letters:

            if letter in frequencies:

                score += frequencies[letter]

        for position, letter in enumerate(word):

            score += position_frequencies[position].get(letter, 0)

        return score


    def choose_guess(self):
        """
        Choose a guess using letter frequency combined with
        positional frequency. If more than one possible answer
        ties for the best score (this is what happens with
        near-identical words like catch/hatch/watch, where
        frequency and position alone can't tell them apart),
        break the tie by picking whichever tied word would
        split the remaining possible answers into the most
        distinct feedback patterns -- i.e. whichever guess is
        most likely to narrow things down the most, regardless
        of which one turns out to be the actual answer.
        """

        if not self.possible_answers:
            return None

        if len(self.possible_answers) == 1:
            return self.possible_answers[0]

        frequencies = self.get_letter_frequencies()
        position_frequencies = self.get_position_frequencies()

        best_score = -1
        best_words = []

        for word in self.possible_answers:

            score = self.score_word(
                word,
                frequencies,
                position_frequencies
            )

            if score > best_score:

                best_score = score
                best_words = [word]

            elif score == best_score:

                best_words.append(word)

        if len(best_words) == 1:
            return best_words[0]

        return self.choose_splitting_guess(best_words)


    def choose_splitting_guess(self, candidates):
        """
        Among a small set of tied candidates, pick whichever
        one would split the current possible answers into the
        most distinct feedback patterns. If none of the tied
        possible answers can fully separate the remaining
        candidates (e.g. catch/hatch/watch, which all look
        identical against each other), fall back to searching
        every legal guess for a better splitter -- including
        words that can't be the answer themselves, purely to
        gather information.
        """

        best_word, best_buckets = self._best_splitter(candidates)

        if best_buckets >= len(self.possible_answers):
            # Already perfectly distinguishes every remaining
            # possible answer -- nothing to gain by looking at
            # words that can't even be the answer.
            return best_word

        guess_word, guess_buckets = self._best_splitter(self.guesses)

        if guess_buckets > best_buckets:
            return guess_word

        return best_word


    def _best_splitter(self, pool):
        """
        Search a pool of candidate guesses and return whichever
        one produces the most distinct feedback patterns against
        the current possible answers, along with that count.
        """

        best_word = None
        best_bucket_count = -1

        for word in pool:

            patterns = set()

            for answer in self.possible_answers:

                patterns.add(
                    self.get_feedback_pattern(word, answer)
                )

            if len(patterns) > best_bucket_count:

                best_bucket_count = len(patterns)
                best_word = word

        return best_word, best_bucket_count


    def get_feedback_pattern(self, guess, answer):
        """
        Get the Wordle feedback pattern for a guess
        against an answer.

        0 = gray
        1 = yellow
        2 = green
        """

        result = [0, 0, 0, 0, 0]

        answer_letters = list(answer)

        # First pass: find green letters
        for i in range(5):

            if guess[i] == answer[i]:

                result[i] = 2

                answer_letters[i] = None


        # Second pass: find yellow letters
        for i in range(5):

            if result[i] == 0:

                if guess[i] in answer_letters:

                    result[i] = 1

                    index = answer_letters.index(
                        guess[i]
                    )

                    answer_letters[index] = None

        return tuple(result)


    def calculate_entropy(self, guess):
        """
        Calculate the expected information gain
        of a guess based on the current possible answers.
        """

        pattern_counts = {}

        for answer in self.possible_answers:

            pattern = self.get_feedback_pattern(
                guess,
                answer
            )

            if pattern not in pattern_counts:

                pattern_counts[pattern] = 0

            pattern_counts[pattern] += 1


        total_answers = len(self.possible_answers)

        entropy = 0

        for count in pattern_counts.values():

            probability = count / total_answers

            entropy -= probability * math.log2(
                probability
            )

        return entropy


    def choose_entropy_guess(self):
        """
        Choose the legal guess with the highest
        expected information gain.

        Unlike the frequency strategy, this considers
        every legal Wordle guess, not just possible answers.
        """

        best_word = None

        best_entropy = -1

        for word in self.guesses:

            entropy = self.calculate_entropy(word)

            if entropy > best_entropy:

                best_entropy = entropy

                best_word = word

        return best_word


    def get_pattern_counts(self, guess):
        """
        Show how many possible answers produce
        each feedback pattern for a guess.
        """

        pattern_counts = {}

        for answer in self.possible_answers:

            pattern = self.get_feedback_pattern(
                guess,
                answer
            )

            if pattern not in pattern_counts:

                pattern_counts[pattern] = 0

            pattern_counts[pattern] += 1

        return pattern_counts


if __name__ == "__main__":

    bot = WordleBot()

    print("================================")
    print("WORDLE BOT - INTERACTIVE MODE")
    print("================================")
    print()

    print("Enter feedback using:")
    print("G = Green")
    print("Y = Yellow")
    print("B = Gray")
    print()

    print("Example: GBBYB")
    print()

    for turn in range(6):

        # Choose the next guess
        guess = bot.choose_guess()

        print("Recommended guess:", guess)

        print(
            "Possible answers remaining:",
            len(bot.possible_answers)
        )

        print()


        # Ask the user for feedback
        feedback_string = input(
            "Enter feedback: "
        ).strip().upper()


        # Make sure the word was five characters
        if len(feedback_string) != 5:

            print(
                "Feedback must contain exactly 5 characters."
            )

            print()

            continue


        # Convert G/Y/B into 2/1/0
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

            print(
                "Use only G, Y, and B."
            )

            print()

            continue


        # Check whether the word was correct
        if feedback == [2, 2, 2, 2, 2]:

            print()

            print("The bot solved the Wordle!")

            print("Answer:", guess)

            break


        # Update possible answers
        bot.update(
            guess,
            feedback
        )


        print()

        print(
            "Possible answers remaining:",
            len(bot.possible_answers)
        )

        print()


        # Check whether the feedback eliminated everything
        if len(bot.possible_answers) == 0:

            print("No possible answers remain.")

            print(
                "There may be an error in the feedback."
            )

            break