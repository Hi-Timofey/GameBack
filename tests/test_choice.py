from db.move import Choice


def test_choice():
    choice = Choice(2)
    # choice.attack = 1

    assert choice.attack == 1  # nosec
