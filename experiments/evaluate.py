import sys

sys.path.append("../wordle")
sys.path.append("../solvers")

from wordle import Wordle
from wordle_bot import WordleBot


def play_game(answer, strategy):
    """
    Play one complete Wordle game.

    answer: the hidden Wordle answer
    strategy: "frequency" or "entropy"

    Returns:
        number of guesses used
        True if the bot won
        False if the bot lost
    """

    game = Wordle(answer)
    bot = WordleBot()

    for turn in range(6):

        # Choose the next guess
        if strategy == "frequency":
            guess = bot.choose_guess()

        elif strategy == "entropy":
            guess = bot.choose_entropy_guess()

        else:
            raise ValueError("Unknown strategy.")

        # Make the guess
        feedback = game.make_guess(guess)

        # Give the feedback to the bot
        bot.update(guess, feedback)

        # Check if the bot won
        if game.is_won():
            return turn + 1, True

    return 6, False


def evaluate_strategy(answers, strategy):
    """
    Test one strategy against every answer.
    """

    results = []

    total = len(answers)

    for index, answer in enumerate(answers):

        guesses, won = play_game(answer, strategy)

        results.append({
            "answer": answer,
            "guesses": guesses,
            "won": won
        })

        # Show progress every 100 games
        if (index + 1) % 100 == 0:
            print(
                strategy,
                ":",
                index + 1,
                "/",
                total
            )

    return results


def summarize_results(results):
    """
    Calculate summary statistics.
    """

    total_games = len(results)

    wins = 0
    total_guesses = 0

    guess_distribution = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0
    }

    for result in results:

        if result["won"]:
            wins += 1

            total_guesses += result["guesses"]
            guess_distribution[result["guesses"]] += 1

    win_rate = wins / total_games
    loss_count = total_games - wins

    if wins > 0:
        average_guesses = total_guesses / wins
    else:
        average_guesses = 0

    print()
    print("Games:", total_games)
    print("Wins:", wins)
    print("Losses:", loss_count)
    print("Win rate:", win_rate)
    print("Average guesses on wins:", average_guesses)

    print()
    print("Guess distribution:")

    for guesses in range(1, 7):

        print(
            guesses,
            "guess(es):",
            guess_distribution[guesses]
        )


if __name__ == "__main__":

    # Load all possible answers
    bot = WordleBot()

    answers = bot.answers

    print("Number of answers:", len(answers))
    print()

    # Test frequency strategy
    print("================================")
    print("FREQUENCY STRATEGY")
    print("================================")

    frequency_results = evaluate_strategy(
        answers,
        "frequency"
    )

    summarize_results(frequency_results)

    # Test entropy strategy
    print()
    print("================================")
    print("ENTROPY STRATEGY")
    print("================================")

    entropy_results = evaluate_strategy(
        answers,
        "entropy"
    )

    summarize_results(entropy_results)
