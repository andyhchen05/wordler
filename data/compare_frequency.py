import sys

sys.path.append("../wordle")

from wordle import Wordle


def load_words(filename):
    words = []

    with open(filename, "r") as file:
        for line in file:
            word = line.strip().lower()

            if len(word) == 5:
                words.append(word)

    return words


class FrequencyBot:

    def __init__(self, answers, unique_bonus):
        self.answers = answers
        self.possible_answers = answers.copy()
        self.unique_bonus = unique_bonus

    def update(self, guess, feedback):
        remaining_answers = []

        for answer in self.possible_answers:
            game = Wordle(answer)

            expected_feedback = game.get_feedback(guess)

            if expected_feedback == feedback:
                remaining_answers.append(answer)

        self.possible_answers = remaining_answers

    def get_letter_frequencies(self):
        frequencies = {}

        for word in self.possible_answers:
            unique_letters = set(word)

            for letter in unique_letters:
                if letter not in frequencies:
                    frequencies[letter] = 0

                frequencies[letter] += 1

        return frequencies

    def score_word(self, word, frequencies):
        unique_letters = set(word)
        unique_count = len(unique_letters)

        # Average (not sum) frequency of the word's unique letters.
        # Summing would already reward words with more unique letters
        # on its own (an extra letter means an extra positive term),
        # which drowns out unique_bonus and makes it have almost no
        # effect. Averaging removes that built-in bias so unique_bonus
        # is the only thing rewarding uniqueness, and can actually
        # change which word wins.
        letter_scores = [
            frequencies[letter]
            for letter in unique_letters
            if letter in frequencies
        ]

        if letter_scores:
            average_score = sum(letter_scores) / len(letter_scores)
        else:
            average_score = 0

        return average_score + (unique_count * self.unique_bonus)

    def choose_guess(self):
        frequencies = self.get_letter_frequencies()

        best_word = None
        best_score = -1

        for word in self.possible_answers:
            score = self.score_word(word, frequencies)

            if score > best_score:
                best_score = score
                best_word = word

        return best_word


def run_game(answer, unique_bonus):
    bot = FrequencyBot(
        answers,
        unique_bonus
    )

    for turn in range(6):

        guess = bot.choose_guess()

        game = Wordle(answer)
        feedback = game.get_feedback(guess)

        if feedback == [2, 2, 2, 2, 2]:
            return turn + 1

        bot.update(guess, feedback)

    return None


def evaluate(unique_bonus):
    total_games = len(answers)

    wins = 0
    losses = 0
    total_guesses = 0

    distribution = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0
    }

    for index, answer in enumerate(answers):

        guesses = run_game(
            answer,
            unique_bonus
        )

        if guesses is not None:
            wins += 1
            total_guesses += guesses
            distribution[guesses] += 1

        else:
            losses += 1

        print(
            "Bonus {}: {}/{} games".format(
                unique_bonus,
                index + 1,
                total_games
            ),
            end="\r"
        )

    print()

    if wins > 0:
        average_guesses = total_guesses / wins
    else:
        average_guesses = 0

    win_rate = (wins / total_games) * 100

    return {
        "bonus": unique_bonus,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "average_guesses": average_guesses,
        "distribution": distribution
    }


def print_results(results):
    print()
    print("================================")
    print("UNIQUE LETTER BONUS:", results["bonus"])
    print("================================")

    print(
        "Wins:",
        results["wins"]
    )

    print(
        "Losses:",
        results["losses"]
    )

    print(
        "Win rate: {:.2f}%".format(
            results["win_rate"]
        )
    )

    print(
        "Average guesses: {:.2f}".format(
            results["average_guesses"]
        )
    )

    print()
    print("Guess distribution:")

    for guesses in range(1, 7):
        count = results["distribution"][guesses]

        print(
            "{} guesses: {}".format(
                guesses,
                count
            )
        )


answers = load_words("../data/answers.txt")


if __name__ == "__main__":

    print("Number of answers:", len(answers))
    print()

    bonuses = [
        0,
        10,
        25,
        50,
        100
    ]

    all_results = []

    for bonus in bonuses:

        results = evaluate(bonus)

        all_results.append(results)

        print_results(results)