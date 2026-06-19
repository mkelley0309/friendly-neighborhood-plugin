#!/usr/bin/env bash
# Friendly Neighborhood — agent color themes for the observation deck.
#
# One palette per character, keyed to their canon colors. Sourced by agent-log.sh.
# 24-bit ("truecolor") ANSI — works in VS Code's integrated terminal and most modern
# terminals. If a terminal can't do truecolor it degrades to the nearest color; the
# text is still readable.
#
# Two functions are exported:
#   agent_group <name>   -> spideys | support | villains | unknown
#   agent_paint <name>   -> prints the SGR escape prefix for that character (no reset)
#
# The BLACK SUIT (symbiote) override is applied by agent-log.sh, not here.

# ── helpers ────────────────────────────────────────────────────────────────────
# fg R G B  -> truecolor foreground escape
_fg() { printf '\033[38;2;%s;%s;%sm' "$1" "$2" "$3"; }
# bg R G B  -> truecolor background escape
_bg() { printf '\033[48;2;%s;%s;%sm' "$1" "$2" "$3"; }
_bold() { printf '\033[1m'; }

agent_group() {
  case "$1" in
    peter|miles|gwen|noir|miguel|ben-reilly|silk|peni|ham|jessica|punk) echo spideys ;;
    uncle-ben|aunt-may|mj|ned|jameson|madame-web|robbie) echo support ;;
    osborn|octavius|venom|sandman|lizard|electro|mysterio|kraven|rhino|vulture|scorpion|carnage|kingpin|cat) echo villains ;;
    *) echo unknown ;;
  esac
}

# Print the color prefix for a character. Distinct hue per spidey + per villain;
# support shares one minimalist muted scheme on purpose (complementary, not loud).
agent_paint() {
  case "$1" in
    # ── Spideys — each a distinct on-character hue ──
    peter)       _bold; _fg 227 38 54 ;;     # classic web-red
    miles)       _bold; _fg 255 60 60; _bg 16 16 20 ;;  # red webbing on near-black
    gwen)        _bold; _fg 246 246 250; _bg 226 47 140 ;; # Spider-Gwen — white on hot pink
    noir)        _bold; _fg 205 205 205; _bg 18 18 18 ;; # monochrome, 1930s
    miguel)      _bold; _fg 56 120 255 ;;     # 2099 blue
    ben-reilly)  _bold; _fg 255 96 28 ;;      # Scarlet Spider orange-red
    silk)        _bold; _fg 214 51 132 ;;     # Silk magenta-red
    peni)        _bold; _fg 255 70 160; _bg 12 14 22 ;;  # SP//dr neon pink on cockpit-dark
    ham)         _bold; _fg 255 150 185 ;;   # Spider-Ham cartoon bubblegum
    jessica)     _bold; _fg 255 196 0; _bg 60 10 16 ;;   # Spider-Woman yellow on dark red
    punk)        _bold; _fg 240 50 90; _bg 10 8 12 ;;    # Spider-Punk spray-paint on black

    # ── Support — ONE minimalist, complementary muted scheme ──
    uncle-ben|aunt-may|mj|ned|jameson|madame-web|robbie) _fg 150 162 178 ;;  # calm slate-gray

    # ── Villains — a palette each, reflecting the character ──
    cat)         _bold; _fg 212 208 222; _bg 26 20 32 ;; # Black Cat — platinum on dark plum
    osborn)      _bold; _fg 120 60 200; _bg 14 24 10 ;;  # goblin purple over green
    octavius)    _bold; _fg 107 160 70 ;;     # doc-ock olive/metallic green
    venom)       _bold; _fg 235 235 240; _bg 8 8 10 ;;   # black suit, white maw
    sandman)     _fg 214 184 122 ;;           # sand tan
    lizard)      _bold; _fg 70 175 100 ;;     # reptile green
    electro)     _bold; _fg 255 221 0; _bg 18 20 40 ;;   # electric yellow on blue
    mysterio)    _bold; _fg 159 84 234 ;;     # fishbowl purple/green mist
    kraven)      _fg 168 112 56 ;;            # hunter earth-brown
    rhino)       _bold; _fg 140 140 145 ;;    # armor gray
    vulture)     _fg 96 150 128 ;;            # weathered steel-green
    scorpion)    _bold; _fg 154 205 50 ;;     # venom yellow-green
    carnage)     _bold; _fg 210 20 20; _bg 10 8 8 ;;     # red on black
    kingpin)     _bold; _fg 236 232 222; _bg 40 44 52 ;; # white suit on slate

    *)           _fg 180 180 180 ;;           # unknown -> neutral
  esac
}

# The BLACK SUIT palette — used for ANY spidey while the symbiote is worn.
# White spider on void-black; deliberately unmistakable.
SUIT_PAINT="$(_bold; _fg 240 240 245; _bg 6 6 8)"
RESET="$(printf '\033[0m')"
