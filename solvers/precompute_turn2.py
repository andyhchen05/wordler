# precompute_turn2.py
#
# One-time offline precomputation of the best TURN-2 guess for
# every state the bot can actually land in.
#
# Why this exists:
#   choose_guess() normally picks turn 2's guess by maximizing
#   entropy -- a proxy for "how well does this guess split the
#   remaining answers." That's a good proxy, but it isn't the
#   real objective. Two guesses can tie (or nearly tie) on
#   entropy while leaving genuinely different average numbers of
#   guesses needed to actually finish the game, because entropy
#   only looks at THIS split, not how easy the resulting buckets
#   are to finish off afterward.
#
#   The real objective -- minimize the average total guesses --
#   can be measured directly by simulation: for a candidate guess,
#   actually play out every answer in the current pool using the
#   normal solver as the continuation policy, and average the
#   guess counts. That's expensive to do live (tens of seconds
#   per candidate), but it only ever needs to be done once per
#   DISTINCT turn-2 state, and there are at most 243 of those
#   (one per possible feedback pattern against the fixed opener),
#   shared across every one of the 3209 games. So it's cheap to
#   precompute once, offline, and expensive only in the sense of
#   "run this script and let it work," not "pay this cost every
#   game."
#
# What it does:
#   1. Find every distinct turn-2 state (grouping all answers by
#      the feedback pattern they'd produce against the opener).
#   2. For each state, shortlist the top N candidates by plain
#      entropy (cheap -- this narrows ~14,800 candidates down to
#      a manageable handful without missing anything competitive).
#   3. For each shortlisted candidate, actually simulate playing
#      out every answer in that state's pool (guess1, candidate,
#      then continue with the normal solver) and measure the true
#      average guesses used.
#   4. Record whichever candidate had the lowest true average as
#      that state's precomputed turn-2 guess.
#   5. Save the whole table to turn2_lookahead.json.
#
# Expected runtime: a couple of hours. This is meant to be run
# once, not as part of a normal evaluation run.

import json
import sys
import time
from collections import Counter

sys.path.append("../wordle")
sys.path.append("../solvers")

from wordler_v2 import WordleEntropyBot


SHORTLIST_SIZE = 10
OUTPUT_PATH = "turn2_lookahead.json"


def play_from(answer, forced_guesses):
    """
    Simulate one game: play the forced_guesses first (in order),
    then continue with the bot's normal policy until solved.
    Returns the total number of guesses used.
    """

    bot = WordleEntropyBot()
    turn = 0

    for guess in forced_guesses:

        feedback = bot.get_feedback_pattern(guess, answer)
        turn += 1

        if feedback == (2, 2, 2, 2, 2):
            return turn

        bot.update(guess, feedback)

    while turn < 6:

        guess = bot.choose_guess()

        feedback = bot.get_feedback_pattern(guess, answer)
        turn += 1

        if feedback == (2, 2, 2, 2, 2):
            return turn

        bot.update(guess, feedback)

    return turn


def rollout_average(pool, forced_guesses):
    """
    Play out every answer in pool with the given forced opening
    guesses, then the normal policy, and return the average
    number of guesses used.
    """

    total = 0

    for answer in pool:
        total += play_from(answer, forced_guesses)

    return total / len(pool)


def main():

    bot = WordleEntropyBot()
    opener = bot.choose_guess()

    print("Opener:", opener)
    print()

    # Group every possible answer by the feedback pattern it
    # would produce against the opener -- this IS the set of
    # distinct turn-2 states.
    states = {}

    for answer in bot.answers:

        pattern = bot.get_feedback_pattern(opener, answer)

        if pattern not in states:
            states[pattern] = []

        states[pattern].append(answer)

    # No point precomputing a state where the pool is already
    # down to 1 answer -- choose_guess already handles that for
    # free, with no search needed.
    states = {
        pattern: pool
        for pattern, pool in states.items()
        if len(pool) > 1
    }

    print("Distinct turn-2 states to precompute:", len(states))
    print()

    lookup = {}

    start_time = time.time()

    for index, (pattern, pool) in enumerate(states.items()):

        state_bot = WordleEntropyBot()
        state_bot.possible_answers = pool
        state_bot.turns_used = 1

        pool_key = frozenset(pool)

        scored = []

        for word in state_bot.guesses:

            entropy, _ = state_bot.get_guess_stats(word, pool_key)

            scored.append((entropy, word))

        scored.sort(reverse=True)

        shortlist = [word for _, word in scored[:SHORTLIST_SIZE]]

        best_word = None
        best_avg = float("inf")

        for candidate in shortlist:

            avg = rollout_average(pool, [opener, candidate])

            if avg < best_avg:
                best_avg = avg
                best_word = candidate

        # Use a plain string key (comma-separated digits) since
        # JSON object keys must be strings, not tuples.
        key = ",".join(str(value) for value in pattern)

        lookup[key] = {
            "guess": best_word,
            "avg_guesses": round(best_avg, 4),
            "pool_size": len(pool)
        }

        elapsed = time.time() - start_time

        print(
            "[{}/{}] pool_size={:4d}  best={}  avg={:.4f}  "
            "elapsed={:.1f}s".format(
                index + 1,
                len(states),
                len(pool),
                best_word,
                best_avg,
                elapsed
            )
        )

        # Save incrementally so a crash or interruption doesn't
        # lose the hours of work already done.
        with open(OUTPUT_PATH, "w") as f:
            json.dump(
                {
                    "opener": opener,
                    "shortlist_size": SHORTLIST_SIZE,
                    "states": lookup
                },
                f,
                indent=2
            )

    print()
    print("Done. Wrote", len(lookup), "states to", OUTPUT_PATH)


if __name__ == "__main__":
    main()