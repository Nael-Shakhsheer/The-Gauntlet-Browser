"""Shared Rune loss on a party wipe; user-selected15% in both game modes."""
WIPE_PERCENT=15


def wipe_loss(runes):return max(0,runes)*WIPE_PERCENT//100
