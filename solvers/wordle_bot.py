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
        """

        frequencies = {}

        for word in self.possible_answers:

            unique_letters = set(word)

            for letter in unique_letters:

                if letter not in frequencies:
                    frequencies[letter] = 0

                frequencies[letter] += 1

        return frequencies


    def score_word(self, word, frequencies):
        """
        Give a word a score based on the frequency
        of its letters among possible answers.
        """

        score = 0

        unique_letters = set(word)

        for letter in unique_letters:

            if letter in frequencies:

                score += frequencies[letter]

        return score


    def choose_guess(self):
        """
        Choose the highest-scoring possible answer
        using letter frequency.
        """

        frequencies = self.get_letter_frequencies()

        best_word = None
        best_score = -1

        for word in self.possible_answers:

            score = self.score_word(
                word,
                frequencies
            )

            if score > best_score:

                best_score = score
                best_word = word

        return best_word


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
