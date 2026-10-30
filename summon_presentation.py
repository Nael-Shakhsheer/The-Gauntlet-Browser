"""Owner-derived animal appearance; never mutates a summon or its statistics.

This small public contract also describes a despawn after its owner has changed
form. The source of truth is the current owner, not whoever receives the state.
"""
ANIMALS = ('lightning_bird', 'fire_wolf', 'ice_bear', 'nature_golem')


def view(room, summon):
    owner = room.get('players', {}).get(summon.get('ownerId'), {})
    animal = summon.get('abilityId')
    ascended = bool(animal in ANIMALS and owner.get('class') == 'Druid'
                    and owner.get('magicRunes', {}).get('ascended'))
    return dict(presentationVersion=1, ownerAscended=ascended,
                appearanceKey=('druid.' + animal + '.' + ('ascended' if ascended else 'normal'))
                if animal in ANIMALS else None)
