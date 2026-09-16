# wordle.py

# 0 = gray
# 1 = yellow
# 2 = green


class Wordle:

    def __init__(self, answer):
        """
        Create a new Wordle game.

        answer: the five-letter answer
        """

        self.answer = answer.lower()
        self.guesses = []
        self.feedback = []

        self.max_guesses = 6
        self.game_over = False
        self.won = False


    def make_guess(self, guess):
        """
        Make a guess and return the feedback.
        """

        guess = guess.lower()

        # Make sure the guess is five letters
        if len(guess) != 5:
            raise ValueError("Guess must be five letters.")

        # Don't allow guesses after the game is over
        if self.game_over:
            raise ValueError("The game is already over.")

        # Generate feedback
        result = self.get_feedback(guess)

        # Store the guess and feedback
        self.guesses.append(guess)
        self.feedback.append(result)

        # Check if the player won
        if result == [2, 2, 2, 2, 2]:
            self.won = True
            self.game_over = True

        # Check if the player ran out of guesses
        elif len(self.guesses) >= self.max_guesses:
            self.game_over = True

        return result


    def get_feedback(self, guess):
        """
        Compare a guess to the answer.

        Returns:
            0 = gray
            1 = yellow
            2 = green
        """

        result = [0, 0, 0, 0, 0]

        # Make a copy so we can remove letters
        # that have already been matched.
        answer_letters = list(self.answer)

        # ------------------------------------------
        # First pass: green letters
        # ------------------------------------------

        for i in range(5):

            if guess[i] == self.answer[i]:

                result[i] = 2
                answer_letters[i] = None


        # ------------------------------------------
        # Second pass: yellow letters
        # ------------------------------------------

        for i in range(5):

            if result[i] == 0:

                if guess[i] in answer_letters:

                    result[i] = 1

                    index = answer_letters.index(guess[i])

                    answer_letters[index] = None


        return result


    def is_game_over(self):
        """
        Return True if the game is finished.
        """

        return self.game_over


    def is_won(self):
        """
        Return True if the game was won.
        """

        return self.won


    def guesses_remaining(self):
        """
        Return the number of guesses remaining.
        """

        return self.max_guesses - len(self.guesses)


def feedback_to_string(feedback):
    """
    Convert numerical feedback into Wordle symbols.
    """

    symbols = {
        0: "⬛",
        1: "🟨",
        2: "🟩"
    }

    result = ""

    for value in feedback:
        result += symbols[value]

    return result