# Wordler

A Python-based Wordle bot that uses statistical analysis and information theory to determine the best possible guesses.

The project started as a simple letter-frequency solver and is being developed into a more sophisticated Wordle-playing agent using positional statistics, entropy, and eventually hybrid strategies.

## Features

### Current

* Loads the official Wordle answer list and legal guess list
* Generates accurate Wordle feedback
* Filters possible answers based on previous guesses
* Calculates letter frequencies among remaining answers
* Selects guesses using letter-frequency scoring
* Calculates information gain using entropy
* Supports interactive play through the terminal
* Can simulate the bot against the complete answer list
* Tracks win rate and guess distribution
* Analyzes letter frequency by position
