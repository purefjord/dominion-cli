# CLI Dominion — Implementation Spec

**Purpose:** This document specifies a playable CLI reimplementation of Dominion (2nd Edition base set) scoped for a single AI agent run. It follows the methodology described in METR's "Observations from two CLI game reimplementation runs with Opus 4.6" (March 2026).

**Target:** A 2-player terminal game, supporting Human vs Human hotseat for MVP and optionally Human vs AI for improved playability and testing.

---

## 1. Game Overview

Dominion is a deck-building card game. Each player starts with an identical weak deck of 10 cards and, over the course of the game, buys better cards from a shared Supply to improve their deck. The player with the most Victory Points (VP) at game end wins.

The game is entirely turn-based. There is no spatial reasoning, no real-time input, and no hidden information beyond each player's hand and deck order.

---

## 2. Core Architecture

### 2.1 Game Zones

Each player has these private zones:
- **Deck** — face-down draw pile. Order matters. Only the owner can see cards.
- **Hand** — cards drawn from the deck. Only the owner can see them (except when revealed by card effects).
- **Play Area** — cards played this turn. Public.
- **Discard Pile** — face-up. Only the top card is public. No player may look through or count any discard pile unless a card effect explicitly instructs them to interact with it (e.g., Harbinger). Players may count cards in their own deck (without looking at fronts) at any time.

Shared zones:
- **Supply** — all card piles available for purchase/gaining. Public (pile sizes are public).
- **Trash** — cards removed from the game. Public. Any player may look through it at any time.

### 2.2 Turn Structure

Each turn has three phases, always in order: **Action → Buy → Clean-up** (ABC).

**Action Phase:**
1. The player starts with 1 Action play.
2. They may play one Action card from their hand, which uses 1 Action play.
3. Some Action cards grant "+N Actions" — these add to the available Action plays.
4. The player may continue playing Action cards as long as they have Action plays remaining.
5. The player may choose to stop playing Actions at any time, even if they have plays remaining.
6. Fully resolve each Action card before playing the next.

**Buy Phase:**
1. The player starts with 1 Buy.
2. First, the player plays any number of Treasure cards from their hand (order does not matter for base set).
3. Treasure cards produce coins: Copper=$1, Silver=$2, Gold=$3.
4. Some Action cards played earlier may have granted "+$N" — this adds to available coins.
5. The player may buy one card from the Supply costing ≤ their available coins. Buying means gaining the card (moving it from Supply to the player's discard pile) and reducing available coins by the cost.
6. If the player has extra Buys (from "+1 Buy" effects), they may buy additional cards, splitting their remaining coins among purchases.
7. Buying is optional. The player may skip buying entirely. Copper costs $0, so a Buy can always be used on Copper.
8. Once the player starts buying, they cannot go back and play more Treasures.

**Clean-up Phase:**
1. All cards in the player's Play Area AND all cards remaining in their hand go to their discard pile.
2. The player draws 5 cards from their deck.
3. If the deck has fewer than 5 cards, shuffle the discard pile, place it face-down as the new deck, then continue drawing.
4. Any unused Actions, Buys, or coins are lost.

### 2.3 Shuffling Rule

Whenever the player needs to draw/look at/reveal cards from their deck and the deck is empty (or has insufficient cards):
1. Shuffle the discard pile.
2. Place it face-down as the new deck.
3. Continue the draw/look/reveal operation.
4. If there still aren't enough cards, do as much as possible.

Important: Do NOT shuffle until a deck operation actually requires it. If a card is placed on top of an empty deck, it simply becomes the only card in the deck (no shuffle triggered).

### 2.4 Game End

The game ends at the END of any player's turn when either:
- The **Province** pile is empty, OR
- **Any 3 or more** Supply piles are empty (any piles at all, including Curses, Copper, Kingdom cards, etc.)

After the game ends, each player counts VP from ALL their cards (hand, deck, discard pile, play area, set aside cards). The player with the most VP wins. Tiebreaker: the player with fewer turns wins. If still tied, shared victory.

---

## 3. Card Definitions

### 3.1 Basic Supply Cards (always present)

| Card | Type | Cost | Effect |
|------|------|------|--------|
| Copper | Treasure | $0 | Worth $1 |
| Silver | Treasure | $3 | Worth $2 |
| Gold | Treasure | $6 | Worth $3 |
| Estate | Victory | $2 | Worth 1 VP |
| Duchy | Victory | $5 | Worth 3 VP |
| Province | Victory | $8 | Worth 6 VP |
| Curse | Curse | $0 | Worth -1 VP |

**Supply quantities (2-player game):**
- Copper/Silver/Gold: use every copy in the box, except Coppers already dealt to players. Copper supply = 60 - (7 × 2) = 46. Silver: 40. Gold: 30.
- Estate: 8 in supply (after dealing 3 each to players)
- Duchy: 8
- Province: 8
- Curse: 10

Each Kingdom card pile: 10 copies, except Victory-type Kingdom cards (Gardens) which use 8 copies in a 2-player game.

### 3.2 Kingdom Cards (26 total in base set, pick 10 per game)

Below are ALL 26 Kingdom cards in the 2nd Edition base set. The implementation should support all 26 and randomly select 10 per game (or allow manual selection).

**Artisan** — Action, Cost $6
- Gain a card to your hand costing up to $5.
- Put a card from your hand onto your deck.
- (The gained card can be the one you put on your deck.)

**Bandit** — Action/Attack, Cost $5
- Gain a Gold from the Supply (to your discard pile).
- Each other player reveals the top 2 cards of their deck, trashes a revealed Treasure other than Copper (they choose which if both qualify), and discards the rest.
- If a player reveals no trashable Treasure, they discard both revealed cards.

**Bureaucrat** — Action/Attack, Cost $4
- Gain a Silver onto the top of your deck (not discard pile).
- Each other player reveals a Victory card from their hand and puts it onto their deck. A player with no Victory cards in hand reveals their hand (proving it).

**Cellar** — Action, Cost $2
- +1 Action.
- Discard any number of cards from your hand, then draw that many cards.
- (The discarded cards may get shuffled in if drawing triggers a reshuffle.)

**Chapel** — Action, Cost $2
- Trash up to 4 cards from your hand.
- (Cannot trash Chapel itself — it's in play, not in hand.)

**Council Room** — Action, Cost $5
- +4 Cards, +1 Buy.
- Each other player draws a card.

**Festival** — Action, Cost $5
- +2 Actions, +1 Buy, +$2.

**Gardens** — Victory, Cost $4
- Worth 1 VP per 10 cards in your deck (rounded down).
- (Count ALL cards you own at game end.)

**Harbinger** — Action, Cost $3
- +1 Card, +1 Action.
- Look through your discard pile. You may put a card from it onto your deck.

**Laboratory** — Action, Cost $5
- +2 Cards, +1 Action.

**Library** — Action, Cost $5
- Draw until you have 7 cards in hand, skipping any Action cards you choose to set aside. Discard the set aside cards afterward.
- (You may choose to keep Action cards; setting aside is optional per Action card encountered.)
- (If you already have 7+ cards, do nothing.)

**Market** — Action, Cost $5
- +1 Card, +1 Action, +1 Buy, +$1.

**Merchant** — Action, Cost $3
- +1 Card, +1 Action.
- The first time you play a Silver this turn, +$1.
- (Multiple Merchants each trigger on the first Silver. Playing a second Silver does not re-trigger.)

[IMPLEMENTATION NOTE: Track turn state as `merchant_triggers_available = number_of_merchants_played_this_turn`. When the first Silver is played, add that many coins and set the counter to 0. No per-card flag needed.]

**Militia** — Action/Attack, Cost $4
- +$2.
- Each other player discards down to 3 cards in hand.
- (Players with 3 or fewer cards do not discard.)

**Mine** — Action, Cost $5
- You may trash a Treasure from your hand. Gain a Treasure to your hand costing up to $3 more than the trashed card.
- (The gained Treasure goes to your hand, not your discard pile. You can play it this turn.)
- (If you have no Treasure to trash, nothing happens.)

**Moat** — Action/Reaction, Cost $2
- +2 Cards.
- When another player plays an Attack card, you may reveal this from your hand to be unaffected by it.
- (Moat stays in your hand after revealing. It can be played normally on your turn.)
- (Moat only protects the revealing player, not other players.)

**Moneylender** — Action, Cost $4
- You may trash a Copper from your hand for +$3.
- (If you don't trash a Copper, you get nothing.)

**Poacher** — Action, Cost $4
- +1 Card, +1 Action, +$1.
- Discard a card per empty Supply pile.
- (Counts ALL empty Supply piles, including Curses, Copper, Kingdom cards, etc.)
- (Draw happens before the discard.)

**Remodel** — Action, Cost $4
- Trash a card from your hand. Gain a card costing up to $2 more than the trashed card.
- (If you have no card to trash, you gain nothing.)
- (The gained card goes to your discard pile.)

**Sentry** — Action, Cost $5
- +1 Card, +1 Action.
- Look at the top 2 cards of your deck. Trash and/or discard any number of them. Put the rest back on top in any order.
- (You can trash both, discard both, put both back, or any combination.)

**Smithy** — Action, Cost $4
- +3 Cards.

**Throne Room** — Action, Cost $4
- You may play an Action card from your hand twice.
- (Resolve the Action fully the first time, then fully the second time.)
- (Playing the Action via Throne Room does not cost an Action play.)
- (If Throne Room targets another Throne Room, you play one Action card twice, then a different Action card twice — NOT one card four times.)
- (Playing an Action card via Throne Room is optional.)

[IMPLEMENTATION NOTE: Throne Room on Throne Room is fully specified by official rules: play one Action twice, then another Action twice — NOT one Action four times. Implement with a recursive resolution stack. The targeted Action is optional; if chosen, resolve it completely the first time, then completely the second time. You cannot insert unrelated cards in between unless the targeted card itself tells you to (e.g., Vassal, or another Throne Room).]

**Vassal** — Action, Cost $3
- +$2.
- Discard the top card of your deck. If it's an Action card, you may play it.
- (Playing it does not use an Action play.)

**Village** — Action, Cost $3
- +1 Card, +2 Actions.

**Witch** — Action/Attack, Cost $5
- +2 Cards.
- Each other player gains a Curse.
- (Curses come from the Supply. Given in turn order, which matters when Curses run low.)
- (When Curses are gone, Witch still draws 2 cards.)

**Workshop** — Action, Cost $3
- Gain a card costing up to $4.
- (The card goes to your discard pile.)
- (You cannot add coins to increase the cost limit.)

---

## 4. Attack and Reaction Timing

When a player plays an Attack card, resolve its effects against each other player in turn order. For each attacked player, before the Attack does anything to them:
1. That player may reveal Moat from their hand.
2. If they reveal Moat, they are unaffected by the Attack. Moat stays in their hand.
3. If they do not reveal Moat (or don't have one), the Attack affects them normally.

This per-player model (check Moat → resolve Attack, for each opponent in turn order) is the correct architecture. In the base set Moat is the only Reaction, but this structure extends cleanly to expansion Reactions.

---

## 5. User Interface Specification

### 5.1 Display Requirements

The CLI should clearly show at all times during a player's turn:
- Whose turn it is (Player 1 or Player 2)
- The current phase (Action / Buy / Clean-up)
- The player's hand (card names, grouped by type is helpful)
- Available Actions, Buys, and Coins
- The Supply: each pile name, cost, and remaining count
- The Trash pile contents (or at least indicate it can be viewed)
- Number of cards in each player's deck and discard pile

### 5.2 Input Design

Use numbered menu choices for all interactions:
- During Action phase: list playable Action cards by number, plus option to skip
- When a card requires choices (e.g., Chapel asks which cards to trash): present numbered options
- During Buy phase: list affordable cards by number, plus option to skip
- For Cellar-type "choose any number" effects: allow comma-separated selection or "none"

### 5.3 Moat Reveal Prompt

When an Attack is played, prompt each other player (who has a Moat in hand) whether they want to reveal it. In a hotseat game, be careful not to reveal one player's hand to the other.

[DESIGN NOTE: In a 2-player hotseat game, both players see the same screen. When Player 1 plays Militia, the game must prompt Player 2 to discard without Player 1 seeing Player 2's hand. Use a "pass the device" prompt with screen clear and "press Enter to continue" before showing the other player's hand. See Section 5.4.]

### 5.4 Screen Clearing

Between turns (and when switching to another player for Attack resolution), clear the terminal and show a "Player N's turn — press Enter to continue" prompt. This prevents the previous player from seeing the next player's hand.

---

## 6. Game Setup Flow

This spec targets a strict 2-player game. 3-4 player support is a later extension.

1. Select 10 Kingdom cards. Options:
   - Random selection from all 26
   - Choose a recommended set (list the 5 preset sets from the rulebook)
   - Manual selection
2. Set up Supply piles with 2-player quantities (see Section 3.1).
3. Give each player 7 Coppers and 3 Estates, shuffled as their starting deck.
4. Each player draws 5 cards.
5. Randomly choose starting player.

**Recommended first-game set:** Cellar, Market, Merchant, Militia, Mine, Moat, Remodel, Smithy, Village, Workshop.

---

## 7. Scoring

At game end, each player counts VP from ALL their cards:
- Estate: 1 VP each
- Duchy: 3 VP each
- Province: 6 VP each
- Curse: -1 VP each
- Gardens: 1 VP per 10 cards the player owns (rounded down)

Display a breakdown showing each card type's contribution and the total.

---

## 8. Implementation Notes

### 8.1 Language

Python is recommended (good string handling, easy terminal I/O, no compilation step). Alternatively, Node.js or Rust would work but offer less prototyping speed.

### 8.2 Data Model Suggestion

```
Player:
  deck: list[Card]       # ordered, index 0 = top
  hand: list[Card]
  play_area: list[Card]
  discard: list[Card]
  actions: int
  buys: int
  coins: int

Supply:
  piles: dict[str, list[Card]]  # card name -> remaining copies

Card:
  name: str
  types: set[str]        # {"Action", "Attack", "Treasure", "Victory", "Reaction", "Curse"}
  cost: int
  vp: int | Callable     # static VP or function (for Gardens)
  effect: Callable       # function(game_state, player) -> None
```

### 8.3 Card Effect Resolution

Each card's effect should be a function that receives the full game state and the acting player, and can:
- Modify the player's Actions/Buys/Coins
- Draw cards
- Prompt the player for choices
- Affect other players (for Attacks, iterating in turn order)
- Trigger Reaction checks (before Attack effects)

### 8.4 Testing Priority

In rough priority order:
1. Shuffling logic (deck/discard cycling) — this is the mechanical foundation
2. Action chaining (+Actions correctly tracked)
3. Buy phase (coins correctly summed from Treasures + Action bonuses)
4. Throne Room interactions (especially Throne Room on Throne Room)
5. Attack/Reaction flow (Moat blocking)
6. Merchant trigger (first Silver bonus)
7. Game end detection (Province empty OR 3 piles empty)
8. Gardens scoring (count all cards at game end)
9. Library (draw-to-7 with optional skip)
10. Sentry (multi-choice trash/discard/keep for 2 cards)

---

## 9. What To Skip (Out of Scope)

- Expansion cards (no Intrigue, Seaside, etc.)
- 3-4 player support (strict 2-player only for MVP)
- Advanced AI opponent (search-based, kingdom-aware, or highly optimized bots)
- Save/load game state
- Network multiplayer
- 5-6 player rules (these require extra base cards)
- Undo functionality
- Card art or color beyond basic ANSI terminal colors

---

## 10. Resolved Rules and Remaining Architecture Decisions

### 10.1 Verified Rules (confirmed against official 2nd Edition rulebook)

All items below were initially flagged as uncertain and have been verified:

- **Copper supply count:** 60 - (7 × players). For 2 players, 46 in supply.
- **Buying Coppers and Curses:** both are legal buys at cost $0. The rules explicitly allow using a Buy with no coins to buy a Copper.
- **Poacher empty pile counting:** counts ALL empty Supply piles, including base cards (Copper, Curses, etc.) and Poacher's own pile. Confirmed by rulebook clarification.
- **Vassal with empty deck:** shuffle discard if needed; if no cards exist after shuffling, nothing happens. Playing the discarded Action is optional and does not use an Action play.
- **Bandit with two trashable Treasures:** the attacked player chooses which to trash.
- **Mine gains to hand:** confirmed exception to the default gain-to-discard rule. The Treasure goes directly to hand and may be played that turn.
- **Bureaucrat with empty Silver pile:** Silver gain fails silently; Attack still resolves against other players. Follows the general rule "do as much as you can."
- **Simultaneous timing:** different players resolve in turn order from the active player. Same player chooses the order of simultaneous effects, even mixing mandatory and optional. This is fully specified in the rulebook and rarely matters in the base set.
- **Throne Room recursion:** fully specified. Throne Room on Throne Room = play one Action twice, then another Action twice. Not one Action four times. Implement with a recursive resolution stack.
- **Merchant trigger:** all Merchants in play fire on the first Silver played. Track as a counter (`merchant_triggers_available`), consume all at once when first Silver is played.
- **Library draw-to-7:** process one card at a time. Action cards may optionally be set aside. Non-Actions always go to hand. Stop at 7 cards in hand. Discard set-aside cards. Set-aside cards are NOT included in reshuffles during resolution.
- **Sentry:** independently choose trash/discard/keep for each of the top 2 cards. If both go back, player chooses order.
- **Harbinger:** temporarily allows looking through discard pile during resolution only.

### 10.2 Implementation Difficulty Tiers

Even though the rules are now fully resolved, some cards are harder to implement correctly than others.

**Tier 1 — Straightforward** (simple stat modifications or draws):
Village, Smithy, Laboratory, Festival, Market, Moat (the draw part), Workshop, Moneylender, Chapel, Council Room

**Tier 2 — Moderate** (require choices, conditional triggers, or non-standard gain locations):
Cellar, Harbinger, Remodel, Artisan, Mine, Militia, Bureaucrat, Bandit, Poacher, Vassal, Sentry, Witch, Merchant

**Tier 3 — Complex** (recursive resolution, draw-until-condition, or multi-step interaction):
Throne Room, Library

### 10.3 Baseline AI Opponent (optional, recommended)

The implementation may support a simple deterministic AI opponent as an alternative to hotseat play. This AI is an implementation feature, not part of the official Dominion rules. A baseline heuristic bot is recommended because hotseat Dominion is awkward to test and less enjoyable to play solo. Big Money is a well-known Dominion baseline strategy documented extensively in the community.

**Design goals:**
- Always take legal actions
- Be deterministic under a fixed RNG seed
- Be simple enough to debug
- Serve as a regression-testing baseline, not a strong competitive AI

**Minimum buy policy (Big Money):**
1. Buy Province if affordable ($8+).
2. Else buy Gold if affordable ($6+).
3. Else buy Silver if affordable ($3+).
4. Else buy nothing (or Copper only if no better purchase is available and a Buy remains).

**Optional endgame improvement:**
- Buy Duchy at $5 once the Province pile has ≤4 remaining. This is a well-known heuristic extension, not required for the baseline.

**Minimum action policy:**
- Play straightforward beneficial Actions automatically when legal and when they require no difficult judgment.
- Automatically reveal Moat when attacked.
- Skip optional complex Action plays unless a simplified policy is implemented.

**Recommended v1 AI-supported Actions** (play automatically):
- Village (+1 Card, +2 Actions — always beneficial)
- Smithy (+3 Cards — always beneficial)
- Laboratory (+2 Cards, +1 Action — always beneficial)
- Festival (+2 Actions, +1 Buy, +$2 — always beneficial)
- Market (+1 Card, +1 Action, +1 Buy, +$1 — always beneficial)
- Merchant (+1 Card, +1 Action — always beneficial)
- Moat (+2 Cards — always beneficial; also auto-reveal on Attacks)
- Witch (+2 Cards, give Curses — always beneficial)
- Council Room (+4 Cards, +1 Buy — almost always beneficial)
- Moneylender (trash a Copper for +$3 — beneficial when Coppers remain in hand)
- Chapel (trash Estates and Coppers early; stop trashing below ~3 Coppers — simple heuristic, high impact)

[NOTE: Chapel is the strongest card in the base set. A Big Money bot that can't use it is noticeably weaker. The heuristic "trash all Estates, trash Coppers down to 3-4" is simple and well-documented.]

**Recommended v1 AI-unsupported or simplified Actions** (skip or use minimal heuristic):
- Cellar (requires evaluating which cards are worth discarding)
- Harbinger (requires evaluating which discard pile card to top-deck)
- Library (draw-to-7 with set-aside decisions)
- Remodel (requires evaluating trash/gain tradeoffs)
- Mine (simple case: always upgrade Copper→Silver→Gold; skip if no Treasure in hand)
- Sentry (requires evaluating trash/discard/keep for 2 cards)
- Throne Room (requires choosing which Action to double)
- Artisan (requires evaluating which card to gain and which to top-deck)
- Bandit (Gold gain is automatic; Attack resolution is automatic)
- Bureaucrat (Silver gain is automatic; Attack resolution is automatic)
- Vassal (play the discarded Action if it's in the supported list; skip otherwise)
- Poacher (play automatically; discard weakest cards by simple priority: Curse > Estate > Copper)
- Militia (+$2 is automatic; Attack resolution handled by opponents)

If the chosen Kingdom contains unsupported AI decision cards, the AI should:
- Still play its Treasures and buy cards legally every turn
- Play any supported Actions it draws
- Skip unsupported Actions rather than crash or make illegal moves

**Determinism requirement:**
The implementation should support a game seed controlling shuffle order, starting player, Kingdom selection, and any AI tie-breaking choices. Seeded runs should produce identical game logs when replayed.

### 10.4 Game Log (required)

The implementation must maintain a structured game log. This is an engineering requirement, not part of the official Dominion rules. A log is required because Dominion resolution is order-sensitive: effects are followed in the order written, players do as much as they can, and many bugs involve hidden zone transitions or shuffle timing. The log is the primary debugging tool.

**Required logged events:**
- Setup: Kingdom selection, starting player, initial decks
- Turn boundaries: turn start (player, turn number), turn end
- Phase transitions: Action / Buy / Clean-up
- Card plays: Action plays, Treasure plays
- Buys: card bought, cost paid, coins remaining
- Gains: card gained, destination zone, source (Supply or other)
- Draws: cards drawn (hidden in public log, visible in debug log)
- Discards: cards discarded, reason
- Trashes: card trashed, reason
- Reveals: cards revealed, to whom
- Deck manipulation: cards put onto deck, shuffles triggered
- Attacks: attack card played, affected players, Moat reveals
- Game end: trigger condition (which piles empty), final scoring breakdown per player

**Log modes:**

*Public log:*
- Shows only publicly visible information
- Safe to display during live play
- Does not reveal hand contents or deck order except when revealed by card effects

*Debug log:*
- Includes full hidden-state detail: exact draws, hand contents, deck order
- Intended for testing and debugging, not normal play

**Recommended format:**

Store log entries as structured event objects (dicts/JSON). Optionally render as human-readable text. Example:

```json
{
  "turn": 7,
  "player": "P1",
  "phase": "Action",
  "event": "play_action",
  "card": "Village",
  "details": {"drew": "Silver"},
  "state_after": {"actions": 2, "buys": 1, "coins": 0, "hand_size": 5}
}
```

**Events requiring exact ordering in the log:**
- Shuffle triggers (which operation caused the shuffle)
- Attack resolution per opponent in turn order
- Merchant first-Silver trigger
- Throne Room target selection and nested resolution steps
- Library set-aside decisions (each card individually)
- Sentry per-card choices
- Game-end pile depletion (which pile(s) triggered the end)

### 10.5 Remaining Architecture Decisions

**Terminal UI library.** Raw print/input is acceptable for MVP. ANSI color codes for card type differentiation (yellow for Treasures, green for Victory, white for Actions, purple for Curses) are recommended but not required. A richer terminal library (e.g., `rich` for Python) is optional polish.

**Mode selection.** At game start, prompt for mode:
- Human vs Human (hotseat)
- Human vs AI (Big Money bot)
- Optionally: AI vs AI (for regression testing — runs silently, outputs log)

**Failure policy for unsupported AI cards.** The AI completes legal Treasure-and-buy turns even when it declines complex Action plays. It never crashes or makes illegal moves.

---

## 11. Recommended Sets for Testing

From the official rulebook:

1. **First Game:** Cellar, Market, Merchant, Militia, Mine, Moat, Remodel, Smithy, Village, Workshop
2. **Size Distortion:** Artisan, Bandit, Bureaucrat, Chapel, Festival, Gardens, Sentry, Throne Room, Witch, Workshop
3. **Deck Top:** Artisan, Bureaucrat, Council Room, Festival, Harbinger, Laboratory, Moneylender, Sentry, Vassal, Village
4. **Sleight of Hand:** Cellar, Council Room, Festival, Gardens, Library, Harbinger, Militia, Poacher, Smithy, Throne Room
5. **Improvements:** Artisan, Cellar, Market, Merchant, Mine, Moat, Moneylender, Poacher, Remodel, Witch

Set 1 is the best for initial testing — it has a good mix of AI-supported and AI-unsupported cards. Set 2 is good for stress-testing complex interactions (Throne Room + Witch, Chapel trashing, Gardens scoring). Set 4 tests Library (the most unusual draw mechanic).

**AI-friendly test set** (all cards are AI-supported or have simple heuristics):
Village, Smithy, Laboratory, Festival, Market, Merchant, Moat, Witch, Moneylender, Chapel.
This set lets you run AI vs AI regression tests without hitting unsupported card decisions.

---

## 12. Success Criteria

The implementation is considered **successful** if:
- A complete game can be played from setup to scoring without crashes
- All 26 Kingdom cards have implemented effects
- The turn structure (ABC) is correctly enforced
- Deck/discard shuffling works correctly over many turns
- Attacks affect other players and Moat blocks them
- The game correctly detects both end conditions (Province empty, 3 piles empty)
- Scoring is accurate, including Gardens
- A structured game log is produced (at minimum, public mode)

The implementation is considered **impressive** if:
- Throne Room chains work correctly, including Throne Room on Throne Room
- Merchant triggers are correct (all Merchants fire on first Silver)
- Library's draw-to-7 with set-aside works
- The UI is comfortable for extended play (30+ minutes)
- A baseline Big Money AI opponent is available
- Seeded runs are reproducible (identical log output for same seed)
- Both public and debug log modes are supported
- AI vs AI mode works for regression testing

---

## Appendix: Revision History

- **v1:** Initial draft by Claude Opus 4.6 based on web research of official rules and community documentation.
- **v2:** Revised after cross-review by GPT 5.4 against the official 2nd Edition rulebook (Rio Grande Games). All LOW-confidence uncertainties resolved. Scope narrowed to strict 2-player. Throne Room recursion and simultaneous timing promoted to fully specified. Merchant implementation simplified. Attack/Reaction timing corrected to per-player model.
- **v3:** Second GPT 5.4 review incorporated. Game log promoted from "nice-to-have" to required engineering feature. Baseline Big Money AI promoted from stretch goal to optional-but-recommended supported mode with concrete buy/action policies. AI-supported card tiers defined. Determinism/seed requirement added. AI-friendly test set added. Success criteria updated to reflect log and AI expectations.
