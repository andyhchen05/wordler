# evaluate_entropy.py
#
# Evaluates wordle_entropy_bot.py by solving every word in answers.txt.
#
# Run from the same directory as wordle_entropy_bot.py:
#
#     python evaluate_entropy.py
#
# The script reports:
#   - number of games solved
#   - number of games failed
#   - average guesses
#   - median guesses
#   - guess distribution
#   - maximum guesses used
#   - words that were not solved within 6 guesses

import statistics
import sys
import time

# Allow us to import wordle_entropy_bot.py
sys.path.append("../wordle")
sys.path.append("../solvers")

from wordler_v2 import WordleEntropyBot


def evaluate_word(answer, verbose=False):
    """
    Solve one Wordle answer using the entropy bot.

    Returns:
        guesses_used
        guess_history

    If the bot does not solve the word within six guesses,
    guesses_used is None.
    """

    bot = WordleEntropyBot()

    guess_history = []

    for turn in range(6):

        guess = bot.choose_guess()

        if guess is None:
            return None, guess_history

        guess_history.append(guess)

        feedback = bot.get_feedback_pattern(
            guess,
            answer
        )

        if feedback == (2, 2, 2, 2, 2):

            return turn + 1, guess_history

        bot.update(
            guess,
            feedback
        )

    return None, guess_history


def evaluate_all(verbose=False):
    """
    Run the entropy solver against every possible answer.
    """

    answers = WordleEntropyBot().answers

    results = []
    failures = []

    start_time = time.time()

    print("================================")
    print("WORDLE ENTROPY BOT EVALUATION")
    print("================================")
    print()

    print("Answers to test:", len(answers))
    print()

    for index, answer in enumerate(answers):

        guesses_used, guess_history = evaluate_word(
            answer,
            verbose=verbose
        )

        if guesses_used is None:

            failures.append(
                (answer, guess_history)
            )

        else:

            results.append(
                (answer, guesses_used, guess_history)
            )

        # Progress indicator
        if (index + 1) % 50 == 0 or index + 1 == len(answers):

            print(
                "Progress:",
                index + 1,
                "/",
                len(answers)
            )

    elapsed = time.time() - start_time

    print()
    print("================================")
    print("RESULTS")
    print("================================")
    print()

    solved = len(results)
    failed = len(failures)
    total = len(answers)

    print("Total games:", total)
    print("Solved:", solved)
    print("Failed:", failed)

    if total > 0:

        solve_rate = solved / total * 100

        print(
            "Solve rate:",
            round(solve_rate, 2),
            "%"
        )

    print()

    if results:

        guess_counts = [
            guesses_used
            for _, guesses_used, _ in results
        ]

        print(
            "Average guesses:",
            round(
                statistics.mean(guess_counts),
                4
            )
        )

        print(
            "Median guesses:",
            statistics.median(guess_counts)
        )

        print(
            "Minimum guesses:",
            min(guess_counts)
        )

        print(
            "Maximum guesses:",
            max(guess_counts)
        )

        print()

        print("Guess distribution:")

        for number in range(1, 7):

            count = guess_counts.count(number)

            percentage = count / total * 100

            print(
                "  ",
                number,
                "guess(es):",
                count,
                "(",
                round(percentage, 2),
                "%)"
            )

    print()

    if failures:

        print("================================")
        print("UNSOLVED WORDS")
        print("================================")
        print()

        for answer, history in failures:

            print(
                answer,
                "->",
                " -> ".join(history)
            )

        print()

    print(
        "Evaluation time:",
        round(elapsed, 2),
        "seconds"
    )

    return results, failures


if __name__ == "__main__":

    evaluate_all()