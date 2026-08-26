---
name: chat-games
description: Play text-based games with your AI agent — 20 Questions, hangman, word games, trivia, riddles, text adventures, and more. Turn any chat into a game night.
version: 1.0.0
author: Postlethwaite Labs
license: MIT
domain: entertainment
subdomain: games
tags:
  - games
  - fun
  - 20-questions
  - hangman
  - trivia
  - riddle
  - text-adventure
---

# Chat Games

A collection of text-based games you can play with your AI agent — no
boards, no downloads, just chat. The agent acts as game master, opponent,
or dungeon master depending on the game.

## When to Use

- You want to kill time or relax with a quick game.
- You're on a break and want something fun in the chat.
- You want to test your agent's reasoning with puzzles and logic games.
- You have friends over and want a party-game feel from the chat.

## Game Library

### 1. Twenty Questions (Agent Guesses)

The user thinks of a person, place, or thing. The agent asks up to 20
yes/no questions to guess it.

- Agent asks ONE question per turn.
- Track questions used (max 20).
- After each answer, narrow down. Make each guess count.
- If the agent guesses before 20, celebrate. If not, admit defeat and
  ask what it was.

**Example flow:**
```
Agent: Is it alive?
You: No
Agent: Is it something found in a kitchen?
...
Agent: Is it a toaster?
You: Yes! 🎉
```

### 2. Twenty Questions (Agent Answers)

The agent thinks of something (pick a category first — animal, object,
place, person). The user asks yes/no questions, the agent answers
honestly and helps keep score of questions used.

### 3. Hangman

The agent picks a word (difficulty: easy 4-6 letters, medium 7-9, hard
10+) and draws the gallows in ASCII.

- Show blanks: `_ _ _ _ _`
- Player guesses one letter at a time.
- Track wrong guesses (max 6 before the figure is complete).
- Show the hangman figure progression.
- Congratulate on win; reveal word gracefully on loss.
- Optionally reverse roles: user picks the word, agent guesses letters.

### 4. Word Ladder

Start word and end word of equal length. Each turn, change ONE letter to
form a new valid word. Try to reach the end word.

```
COLD → CORD → CARD → WARD → WARM
```
- Agent provides the start/end pair and validates each step.
- Optionally let the agent play against the user.

### 5. Anagrams

The agent scrambles a word; the user unscrambles it.

- Give 3 clues if needed (category, letter count, first letter).
- Reverse: user scrambles a word, agent solves.

### 6. Trivia

Pick a category: tech, history, science, geography, movies, music,
sports, or general. The agent asks questions one at a time.

- One question per turn, wait for the answer.
- Keep score across the session.
- Difficulty: easy/medium/hard.
- Optionally let the user quiz the agent.

### 7. Riddles & Logic Puzzles

The agent presents classic riddles, lateral thinking puzzles, or logic
grids. Hints available on request.

- Reveal the answer when the user gives up.
- Rate the user's answer as correct / close / wrong.

### 8. Text Adventure

The agent builds an interactive story set in a theme of the user's
choice (space, dungeon, mystery, pirate ship, cyberpunk city...).

- Each turn: describe the scene (2-4 sentences), then give 2-4
  choices like `[1] Open the door [2] Look around [3] Check your pack`.
- Track inventory, health, and location simply.
- Keep state consistent between turns — locations and items must
  stay put.
- Include a few secret/puzzle branches for replayability.

### 9. Story Dice

The user rolls 3-5 random elements (character, place, object, conflict)
and the agent weaves them into a short story or the start of one.

### 10. Would You Rather / This or That

The agent poses fun or diabolical either/or questions. Round-robin
option: user answers, then the tables turn and the agent defends the
opposite choice.

## Rules of Engagement

- Keep games **short and snappy** — one prompt/question per turn.
- Use emoji sparingly for flavour, never for decoration overload.
- If the user types something off-game, note it and ask if they meant
  to answer in-game or switch games.
- Track score/state in the conversation; a run of 3+ games in one
  session may suggest checking in: "Want to keep going or call it?"
- Be a good sport — losing gracefully is part of the fun.

## Game Master Tips

- **Always confirm the category/theme first** for guessing games.
- **Never make the answer obvious from the first hint** — pace the
  challenge.
- **For hard puzzles**, hint after 2-3 failed attempts, don't force the
  reveal until asked.
- **Text adventures**: describe sensory details (what you see, hear,
  smell) — it makes the world feel alive.
- **Keep score visibly** (e.g. `You: 4 • Agent: 3`).

## Privacy

Everything happens in the chat — no accounts, no tracking, no data
stored anywhere. All state lives in the conversation itself.